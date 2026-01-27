from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc
from fastapi import HTTPException
from typing import List, Optional

# Models
from app.models.material_receipt import MaterialReceipt, MaterialReceiptDetail
from app.models.purchase_order import PurchaseOrderDetail, POStatus, PurchaseOrderHeader
from app.models.batch import Batch, BatchQCStatus
from app.models.inventory import InventoryStock # Import để type hinting nếu cần

# Schemas
from app.schemas.material_receipt_schema import (
    MaterialReceiptCreate, 
    MaterialReceiptUpdate, 
    MaterialReceiptDetailCreate,
    MaterialReceiptDetailUpdate,
    MaterialReceiptFilter
)
from app.schemas.batch_schema import BatchCreate

# Services
from app.services.batch_service import BatchService
from app.services.inventory_service import InventoryService

class MaterialReceiptService:
    def __init__(self, db: Session):
        self.db = db
        # Khởi tạo các service con để tái sử dụng logic
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
        # 1. Validate
        if self.get_by_number(obj_in.receipt_number):
            raise HTTPException(status_code=400, detail=f"Mã phiếu nhập {obj_in.receipt_number} đã tồn tại.")

        # 2. Tạo Header
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
        self.db.flush() # Lấy receipt_id

        # 3. Tạo Details + Batch + Inventory (Tích hợp chặt chẽ)
        if obj_in.details:
            for detail_in in obj_in.details:
                # A. Tạo Detail & Update PO
                new_detail = self._create_detail_instance(db_header.receipt_id, detail_in, db_header.po_header_id)
                self.db.flush() # Lấy detail_id

                # B. Tạo Batch (Auto Link) - Hàm này trả về Batch object
                batch = self._sync_batch_for_detail(new_detail)
                
                # C. [OPTIMIZED] Tăng Tồn Kho ngay lập tức
                # Lưu ý: Dùng warehouse_id từ Header
                if batch:
                    self.inventory_service.increase_stock(
                        material_id=new_detail.material_id,
                        warehouse_id=db_header.warehouse_id,
                        batch_id=batch.batch_id,
                        quantity=new_detail.received_quantity_kg
                    )

        # 4. Check đóng PO
        if obj_in.po_header_id:
            self._check_and_close_po(obj_in.po_header_id)

        self.db.commit()
        self.db.refresh(db_header)
        return db_header

    def update(self, receipt_id: int, obj_in: MaterialReceiptUpdate) -> MaterialReceipt:
        db_obj = self.get(receipt_id)
        if not db_obj:
            raise HTTPException(status_code=404, detail="Phiếu nhập không tồn tại.")

        # Check nếu đổi warehouse_id (Rất nguy hiểm, cần xử lý chuyển kho)
        # Ở đây ta giả định không cho đổi kho khi đã nhập, hoặc update đơn giản thông tin text
        old_warehouse_id = db_obj.warehouse_id

        update_data = obj_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        self.db.add(db_obj)
        self.db.flush()

        # Nếu warehouse thay đổi, logic inventory sẽ rất phức tạp (Trừ kho cũ, cộng kho mới).
        # Để an toàn, nếu warehouse thay đổi, ta chặn hoặc phải implement logic move stock.
        if obj_in.warehouse_id and obj_in.warehouse_id != old_warehouse_id:
             raise HTTPException(status_code=400, detail="Không được phép đổi Kho của phiếu nhập đã tạo. Hãy tạo phiếu điều chuyển.")

        # Đồng bộ lại thông tin Batch (nếu cần)
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
        warehouse_id = receipt.warehouse_id

        # Loop qua từng detail để hoàn tác (Revert)
        detail: MaterialReceiptDetail 
        for detail in receipt.details:
            # 1. Revert PO
            if receipt.po_header_id:
                self._update_po_received_quantity(
                    po_id=receipt.po_header_id,
                    material_id=detail.material_id, 
                    quantity_delta_kg= -detail.received_quantity_kg 
                )
            
            # 2. Revert Inventory (Trừ kho)
            batch = self.db.query(Batch).filter(Batch.receipt_detail_id == detail.detail_id).first()
            if batch:
                # Tăng số âm = Trừ kho
                self.inventory_service.increase_stock(
                    material_id=detail.material_id,
                    warehouse_id=warehouse_id,
                    batch_id=batch.batch_id,
                    quantity= -detail.received_quantity_kg 
                )
                
                # 3. Xóa Batch (Nếu tồn kho đã về 0 và chưa dùng)
                # Logic xóa batch an toàn: check xem stock có > 0 hay ko
                # Nhưng ở đây ta cứ để database lo việc cascade hoặc giữ lại batch rỗng
                try:
                    self.db.delete(batch)
                except:
                    pass

        if receipt.po_header_id:
            self._check_and_close_po(receipt.po_header_id)

        self.db.delete(receipt)
        self.db.commit()
        return {"message": "Đã xóa phiếu nhập, hoàn trả PO và trừ tồn kho."}

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

        # 1. Tạo Detail & Update PO
        new_detail = self._create_detail_instance(receipt.receipt_id, detail_in, receipt.po_header_id)
        self.db.flush()

        # 2. Tạo Batch
        batch = self._sync_batch_for_detail(new_detail)

        # 3. [OPTIMIZED] Tăng Inventory
        if batch:
            self.inventory_service.increase_stock(
                material_id=new_detail.material_id,
                warehouse_id=receipt.warehouse_id,
                batch_id=batch.batch_id,
                quantity=new_detail.received_quantity_kg
            )
        
        # 4. Check PO
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
        
        # 1. Tính delta (chênh lệch) số lượng
        qty_delta = 0.0
        if obj_in.received_quantity_kg is not None:
            qty_delta = obj_in.received_quantity_kg - db_detail.received_quantity_kg

        # 2. Update DB Detail
        update_data = obj_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_detail, field, value)
        self.db.add(db_detail)
        self.db.flush()

        # 3. Update PO (nếu có delta)
        if receipt.po_header_id and qty_delta != 0:
            self._update_po_received_quantity(
                po_id=receipt.po_header_id,
                material_id=db_detail.material_id,
                quantity_delta_kg=qty_delta
            )
            self._check_and_close_po(receipt.po_header_id)

        # 4. [OPTIMIZED] Update Inventory (nếu có delta)
        # Lấy batch liên quan
        batch = self._sync_batch_for_detail(db_detail) # Sync lại phòng khi user sửa thông tin lô
        if batch and qty_delta != 0:
            self.inventory_service.increase_stock(
                material_id=db_detail.material_id,
                warehouse_id=receipt.warehouse_id,
                batch_id=batch.batch_id,
                quantity=qty_delta # Cộng thêm phần chênh lệch (nếu âm thì trừ đi)
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
        
        # Lấy batch trước khi xóa detail
        batch = self.db.query(Batch).filter(Batch.receipt_detail_id == detail_id).first()

        # 1. Revert Inventory
        if batch:
            self.inventory_service.increase_stock(
                material_id=db_detail.material_id,
                warehouse_id=receipt.warehouse_id,
                batch_id=batch.batch_id,
                quantity= -db_detail.received_quantity_kg # Trừ kho
            )

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
            try:
                self.db.delete(batch)
            except:
                batch.is_active = False # Soft delete nếu ko xóa cứng được
                self.db.add(batch)

        self.db.delete(db_detail)
        self.db.commit()
        return {"message": "Đã xóa chi tiết, cập nhật PO và trừ tồn kho."}

    # =========================================================================
    # INTERNAL HELPERS
    # =========================================================================

    def _create_detail_instance(self, receipt_id: int, detail_in: MaterialReceiptDetailCreate, po_id: Optional[int]):
        # Tạo object nhưng chưa commit để dùng session chung
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
        
        # Nếu có location trong schema (tùy chỉnh thêm)
        if hasattr(detail_in, 'location') and hasattr(db_detail, 'location'):
             setattr(db_detail, 'location', getattr(detail_in, 'location'))

        self.db.add(db_detail)

        if po_id:
            self._update_po_received_quantity(
                po_id=po_id,
                material_id=detail_in.material_id,
                quantity_delta_kg=detail_in.received_quantity_kg
            )
        return db_detail

    def _sync_batch_for_detail(self, detail: MaterialReceiptDetail) -> Optional[Batch]:
        """
        Tạo hoặc cập nhật Batch dựa trên Receipt Detail.
        Trả về Batch Object để dùng cho Inventory.
        """
        supplier_batch = detail.supplier_batch_no if detail.supplier_batch_no else f"NO-BATCH-{detail.detail_id}"
        
        # Lấy location từ detail (nếu có, để lưu vào Batch phục vụ tìm kiếm)
        current_location = getattr(detail, 'location', None)

        existing_batch = self.db.query(Batch).filter(
            Batch.receipt_detail_id == detail.detail_id
        ).first()

        if existing_batch:
            # Update nếu thông tin thay đổi
            if existing_batch.supplier_batch_no != supplier_batch:
                existing_batch.supplier_batch_no = supplier_batch
            
            if existing_batch.material_id != detail.material_id:
                existing_batch.material_id = detail.material_id
            
            if hasattr(detail, 'origin_country') and existing_batch.origin_country != detail.origin_country:
                existing_batch.origin_country = detail.origin_country

            self.db.add(existing_batch)
            return existing_batch
        else:
            # Create New Batch
            batch_in = BatchCreate(
                supplier_batch_no=supplier_batch,
                material_id=detail.material_id,
                qc_status=BatchQCStatus.PENDING, # Mặc định là Pending chờ QC
                is_active=True,
                receipt_detail_id=detail.detail_id,
                # Truyền thêm origin_country từ detail nếu có
                origin_country=getattr(detail, 'origin_country', None),
                # Truyền location nếu batch schema hỗ trợ
                location=current_location 
            )
            # Sử dụng BatchService để tạo (để tận dụng logic sinh mã nội bộ)
            return self.batch_service.create(batch_in)

    def _update_po_received_quantity(self, po_id: int, material_id: int, quantity_delta_kg: float):
        po_details = self.db.query(PurchaseOrderDetail).filter(
            PurchaseOrderDetail.po_id == po_id,
            PurchaseOrderDetail.material_id == material_id
        ).all()

        if not po_details:
            return

        target_detail: PurchaseOrderDetail = po_details[0]
        current = target_detail.received_quantity or 0.0
        new_qty = current + quantity_delta_kg
        target_detail.received_quantity = max(0.0, new_qty)
        self.db.add(target_detail)

    def _check_and_close_po(self, po_id: int):
        po_header = self.db.query(PurchaseOrderHeader).filter(PurchaseOrderHeader.po_id == po_id).first()
        if not po_header:
            return

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