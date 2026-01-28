from sqlalchemy.orm import Session
from sqlalchemy import or_, desc
from fastapi import HTTPException
from typing import List, Optional
from datetime import datetime

# Models
from app.models.material_receipt import MaterialReceipt, MaterialReceiptDetail
from app.models.purchase_order import PurchaseOrderDetail, POStatus, PurchaseOrderHeader
from app.models.batch import Batch, BatchQCStatus
from app.models.inventory import InventoryStock

# Schemas
from app.schemas.material_receipt_schema import (
    MaterialReceiptCreate, 
    MaterialReceiptUpdate, 
    MaterialReceiptDetailCreate,
    MaterialReceiptDetailUpdate,
    MaterialReceiptFilter
)
from app.schemas.batch_schema import BatchCreate
from app.services.batch_service import BatchService
from app.services.inventory_service import InventoryService

class MaterialReceiptService:
    def __init__(self, db: Session):
        self.db = db
        self.batch_service = BatchService(db)
        self.inventory_service = InventoryService(db)

    # =========================================================================
    # QUẢN LÝ PHIẾU NHẬP (HEADER)
    # =========================================================================
    
    def get(self, receipt_id: int) -> Optional[MaterialReceipt]:
        return self.db.query(MaterialReceipt).filter(MaterialReceipt.receipt_id == receipt_id).first()

    def get_by_number(self, receipt_number: str) -> Optional[MaterialReceipt]:
        return self.db.query(MaterialReceipt).filter(MaterialReceipt.receipt_number == receipt_number).first()

    def get_multi(self, skip: int = 0, limit: int = 100, filter_param: Optional[MaterialReceiptFilter] = None) -> List[MaterialReceipt]:
        query = self.db.query(MaterialReceipt)

        if filter_param:
            if filter_param.po_id:
                query = query.filter(MaterialReceipt.po_header_id == filter_param.po_id)
            if filter_param.declaration_id:
                query = query.filter(MaterialReceipt.declaration_id == filter_param.declaration_id)
            if filter_param.from_date:
                query = query.filter(MaterialReceipt.receipt_date >= filter_param.from_date)
            if filter_param.to_date:
                query = query.filter(MaterialReceipt.receipt_date <= filter_param.to_date)
            if filter_param.search:
                search = f"%{filter_param.search}%"
                query = query.filter(
                    or_(
                        MaterialReceipt.receipt_number.ilike(search),
                        MaterialReceipt.container_no.ilike(search),
                        MaterialReceipt.seal_no.ilike(search)
                    )
                )

        return query.order_by(desc(MaterialReceipt.receipt_date)).offset(skip).limit(limit).all()

    def create(self, obj_in: MaterialReceiptCreate) -> MaterialReceipt:
        if self.get_by_number(obj_in.receipt_number):
            raise HTTPException(status_code=400, detail=f"Mã phiếu nhập {obj_in.receipt_number} đã tồn tại.")

        db_header = MaterialReceipt(
            receipt_number=obj_in.receipt_number,
            receipt_date=obj_in.receipt_date,
            po_header_id=obj_in.po_header_id,
            declaration_id=obj_in.declaration_id,
            warehouse_id=obj_in.warehouse_id,
            container_no=obj_in.container_no,
            seal_no=obj_in.seal_no,
            note=obj_in.note,
            created_by=obj_in.created_by
        )
        self.db.add(db_header)
        self.db.flush() 

        if obj_in.details:
            for detail_in in obj_in.details:
                new_detail = self._create_detail_instance(db_header.receipt_id, detail_in, db_header.po_header_id)
                self.db.flush() 
                batch = self._sync_batch_for_detail(new_detail)
                if batch:
                    self.inventory_service.increase_stock(
                        material_id=new_detail.material_id,
                        warehouse_id=db_header.warehouse_id,
                        batch_id=batch.batch_id,
                        quantity=new_detail.received_quantity_kg
                    )

        if obj_in.po_header_id:
            self._check_and_close_po(obj_in.po_header_id)

        self.db.commit()
        self.db.refresh(db_header)
        return db_header

    def update(self, receipt_id: int, obj_in: MaterialReceiptUpdate) -> MaterialReceipt:
        db_obj = self.get(receipt_id)
        if not db_obj:
            raise HTTPException(status_code=404, detail="Phiếu nhập không tồn tại.")

        update_data = obj_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        self.db.add(db_obj)
        self.db.flush()
        
        # Đồng bộ lại Batch nếu cần
        for detail in db_obj.details:
            self._sync_batch_for_detail(detail)

        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def delete(self, receipt_id: int):
        db_obj = self.get(receipt_id)
        if not db_obj:
            raise HTTPException(status_code=404, detail="Phiếu nhập không tồn tại.")
        
        receipt: MaterialReceipt = db_obj

        # Duyệt qua từng chi tiết để dọn dẹp dữ liệu liên quan
        if receipt.details:
            for detail in receipt.details:
                # 1. Revert PO Quantity (Trả lại số lượng cho đơn mua hàng)
                if receipt.po_header_id:
                    self._update_po_received_quantity(
                        po_id=receipt.po_header_id,
                        material_id=detail.material_id, 
                        quantity_delta_kg= -detail.received_quantity_kg 
                    )
                
                # 2. Xóa InventoryStock & Batch
                batch = self.db.query(Batch).filter(Batch.receipt_detail_id == detail.detail_id).first()
                if batch:
                    stock = self.db.query(InventoryStock).filter(InventoryStock.batch_id == batch.batch_id).first()
                    if stock:
                        self.db.delete(stock)
                    self.db.delete(batch)

        # 3. Cập nhật trạng thái PO
        if receipt.po_header_id:
            self._check_and_close_po(receipt.po_header_id)

        # 4. Xóa phiếu nhập
        self.db.delete(receipt)
        
        self.db.commit()
        return {"message": "Đã xóa phiếu nhập, cập nhật lại PO và xóa tồn kho liên quan."}

    # =========================================================================
    # QUẢN LÝ CHI TIẾT (DETAIL)
    # =========================================================================

    def get_detail(self, detail_id: int) -> Optional[MaterialReceiptDetail]:
        return self.db.query(MaterialReceiptDetail).filter(MaterialReceiptDetail.detail_id == detail_id).first()

    def add_detail(self, receipt_id: int, detail_in: MaterialReceiptDetailCreate) -> MaterialReceiptDetail:
        receipt_obj = self.get(receipt_id)
        if not receipt_obj:
            raise HTTPException(status_code=404, detail="Phiếu nhập Header không tồn tại.")
        
        receipt: MaterialReceipt = receipt_obj

        # 1. Tạo Detail
        new_detail = self._create_detail_instance(receipt.receipt_id, detail_in, receipt.po_header_id)
        self.db.flush()

        # 2. Tạo Batch
        batch = self._sync_batch_for_detail(new_detail)

        # 3. Tăng Inventory
        if batch:
            self.inventory_service.increase_stock(
                material_id=new_detail.material_id,
                warehouse_id=receipt.warehouse_id,
                batch_id=batch.batch_id,
                quantity=new_detail.received_quantity_kg
            )
        
        if receipt.po_header_id:
             self._check_and_close_po(receipt.po_header_id)

        self.db.commit()
        self.db.refresh(new_detail)
        return new_detail

    def update_detail(self, detail_id: int, obj_in: MaterialReceiptDetailUpdate) -> MaterialReceiptDetail:
        db_detail = self.get_detail(detail_id)
        if not db_detail:
            raise HTTPException(status_code=404, detail="Chi tiết phiếu nhập không tồn tại.")

        receipt_obj = db_detail.header 
        receipt: MaterialReceipt = receipt_obj
        
        # 1. Tính delta
        qty_delta = 0.0
        if obj_in.received_quantity_kg is not None:
            qty_delta = obj_in.received_quantity_kg - db_detail.received_quantity_kg

        # 2. Update DB
        update_data = obj_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_detail, field, value)
        
        # [FIX] Gán lại location/origin_country vào object db_detail (nếu có trong input)
        # để hàm _sync_batch_for_detail có thể đọc được
        if hasattr(obj_in, 'location'): db_detail.location = obj_in.location
        if hasattr(obj_in, 'origin_country'): db_detail.origin_country = obj_in.origin_country

        self.db.add(db_detail)
        self.db.flush()

        # 3. Update PO
        if receipt.po_header_id and qty_delta != 0:
            self._update_po_received_quantity(
                po_id=receipt.po_header_id,
                material_id=db_detail.material_id,
                quantity_delta_kg=qty_delta
            )
            self._check_and_close_po(receipt.po_header_id)

        # 4. Update Inventory & Batch
        batch = self._sync_batch_for_detail(db_detail)
        if batch and qty_delta != 0:
            self.inventory_service.increase_stock(
                material_id=db_detail.material_id,
                warehouse_id=receipt.warehouse_id,
                batch_id=batch.batch_id,
                quantity=qty_delta 
            )

        self.db.commit()
        self.db.refresh(db_detail)
        return db_detail

    def delete_detail(self, detail_id: int):
        db_detail = self.get_detail(detail_id)
        if not db_detail:
            raise HTTPException(status_code=404, detail="Chi tiết phiếu nhập không tồn tại.")

        receipt_obj = db_detail.header
        receipt: MaterialReceipt = receipt_obj
        
        batch = self.db.query(Batch).filter(Batch.receipt_detail_id == detail_id).first()

        # 1. Xóa InventoryStock trước
        if batch:
            stock = self.db.query(InventoryStock).filter(InventoryStock.batch_id == batch.batch_id).first()
            if stock:
                self.db.delete(stock)

        # 2. Revert PO
        if receipt.po_header_id:
            self._update_po_received_quantity(
                po_id=receipt.po_header_id,
                material_id=db_detail.material_id,
                quantity_delta_kg= -db_detail.received_quantity_kg 
            )
            self._check_and_close_po(receipt.po_header_id)

        # 3. Xóa Batch
        if batch:
            self.db.delete(batch)

        # 4. Xóa Detail
        self.db.delete(db_detail)
        
        self.db.commit()
        return {"message": "Đã xóa chi tiết và cập nhật kho."}

    # =========================================================================
    # INTERNAL HELPERS
    # =========================================================================

    def _create_detail_instance(self, receipt_id: int, detail_in: MaterialReceiptDetailCreate, po_id: Optional[int]):
        db_detail = MaterialReceiptDetail(
            receipt_id=receipt_id,
            material_id=detail_in.material_id,
            po_quantity_kg=detail_in.po_quantity_kg,
            po_quantity_cones=detail_in.po_quantity_cones,
            received_quantity_kg=detail_in.received_quantity_kg,
            received_quantity_cones=detail_in.received_quantity_cones,
            number_of_pallets=detail_in.number_of_pallets,
            supplier_batch_no=detail_in.supplier_batch_no,
            note=detail_in.note
        )
        
        # [FIX QUAN TRỌNG] Gán thuộc tính Location và Origin vào object Python (Transient)
        # Dù bảng MaterialReceiptDetail trong DB không có cột này, 
        # nhưng ta cần gán vào object để truyền sang hàm _sync_batch_for_detail
        if hasattr(detail_in, 'location'):
             db_detail.location = detail_in.location
        
        if hasattr(detail_in, 'origin_country'):
             db_detail.origin_country = detail_in.origin_country

        self.db.add(db_detail)

        if po_id:
            self._update_po_received_quantity(
                po_id=po_id,
                material_id=detail_in.material_id,
                quantity_delta_kg=detail_in.received_quantity_kg
            )
        return db_detail

    def _sync_batch_for_detail(self, detail: MaterialReceiptDetail) -> Optional[Batch]:
        """Tạo/Update Batch và trả về object"""
        supplier_batch = detail.supplier_batch_no if detail.supplier_batch_no else f"NO-BATCH-{detail.detail_id}"
        
        # [FIX] Lấy thông tin an toàn bằng getattr để tránh lỗi nếu object không có thuộc tính
        current_location = getattr(detail, 'location', None)
        current_origin = getattr(detail, 'origin_country', None)
        
        existing_batch = self.db.query(Batch).filter(
            Batch.receipt_detail_id == detail.detail_id
        ).first()

        if existing_batch:
            is_changed = False
            if existing_batch.supplier_batch_no != supplier_batch:
                existing_batch.supplier_batch_no = supplier_batch
                is_changed = True
            
            if existing_batch.material_id != detail.material_id:
                existing_batch.material_id = detail.material_id
                is_changed = True
            
            # Update Origin & Location nếu có giá trị mới
            if current_origin is not None and existing_batch.origin_country != current_origin:
                existing_batch.origin_country = current_origin
                is_changed = True

            if current_location is not None and existing_batch.location != current_location:
                existing_batch.location = current_location
                is_changed = True

            if is_changed:
                self.db.add(existing_batch)
            
            return existing_batch
        else:
            # Create New Batch
            batch_in = BatchCreate(
                supplier_batch_no=supplier_batch,
                material_id=detail.material_id,
                qc_status=BatchQCStatus.PENDING,
                is_active=True,
                receipt_detail_id=detail.detail_id,
                # Truyền đúng thông tin location và origin
                origin_country=current_origin,
                location=current_location 
            )
            return self.batch_service.create(batch_in)

    def _update_po_received_quantity(self, po_id: int, material_id: int, quantity_delta_kg: float):
        po_details = self.db.query(PurchaseOrderDetail).filter(
            PurchaseOrderDetail.po_id == po_id,
            PurchaseOrderDetail.material_id == material_id
        ).all()

        if not po_details: return

        target_detail: PurchaseOrderDetail = po_details[0]
        current = target_detail.received_quantity or 0.0
        new_qty = current + quantity_delta_kg
        target_detail.received_quantity = max(0.0, new_qty)
        self.db.add(target_detail)

    def _check_and_close_po(self, po_id: int):
        po_header = self.db.query(PurchaseOrderHeader).filter(PurchaseOrderHeader.po_id == po_id).first()
        if not po_header: return

        all_received = True
        has_received_any = False
        
        detail: PurchaseOrderDetail
        for detail in po_header.details:
            ordered = detail.quantity or 0.0
            received = detail.received_quantity or 0.0
            
            if received > 0.01: has_received_any = True
            if received < (ordered - 0.01): all_received = False
        
        if all_received:
            po_header.status = POStatus.COMPLETED
        elif has_received_any:
            po_header.status = POStatus.PARTIAL
        else:
            if po_header.status != POStatus.DRAFT:
                po_header.status = POStatus.CONFIRMED 
        
        self.db.add(po_header)

    def generate_next_receipt_number(self) -> str:
        now = datetime.now()
        prefix = now.strftime("%Y/%m-") 
        
        last_receipt = self.db.query(MaterialReceipt.receipt_number)\
            .filter(MaterialReceipt.receipt_number.like(f"{prefix}%"))\
            .order_by(desc(MaterialReceipt.receipt_number))\
            .first()
        
        if not last_receipt:
            return f"{prefix}001"
        
        try:
            last_number_str = last_receipt[0]
            sequence_part = last_number_str.split('-')[-1]
            next_sequence = int(sequence_part) + 1
            return f"{prefix}{next_sequence:03d}"
        except (ValueError, IndexError):
            return f"{prefix}001"