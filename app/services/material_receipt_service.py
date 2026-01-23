from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc
from fastapi import HTTPException
from typing import List, Optional

from app.models.material_receipt import MaterialReceipt, MaterialReceiptDetail
from app.models.purchase_order import PurchaseOrderDetail, POStatus, PurchaseOrderHeader
from app.models.batch import Batch, BatchQCStatus

from app.schemas.material_receipt_schema import (
    MaterialReceiptCreate, 
    MaterialReceiptUpdate, 
    MaterialReceiptDetailCreate,
    MaterialReceiptDetailUpdate,
    MaterialReceiptFilter
)
from app.schemas.batch_schema import BatchCreate, BatchUpdate
from app.services.batch_service import BatchService

class MaterialReceiptService:
    def __init__(self, db: Session):
        self.db = db
        self.batch_service = BatchService(db)

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

        # 1. Tạo Header
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
        self.db.flush() # Lấy ID

        # 2. Tạo Details
        if obj_in.details:
            for detail_in in obj_in.details:
                self._create_detail_instance(db_header.receipt_id, detail_in, db_header.po_header_id)

        # 3. Cập nhật trạng thái PO
        if obj_in.po_header_id:
            self._check_and_close_po(obj_in.po_header_id)

        self.db.commit()
        self.db.refresh(db_header)

        # 4. [AUTO LINK] Tạo Batch tự động cho từng dòng chi tiết
        self._sync_batches_from_receipt(db_header)

        return db_header

    def update(self, receipt_id: int, obj_in: MaterialReceiptUpdate) -> MaterialReceipt:
        db_obj = self.get(receipt_id)
        if not db_obj:
            raise HTTPException(status_code=404, detail="Phiếu nhập không tồn tại.")

        # 1. Update Header
        update_data = obj_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)

        # 2. [AUTO LINK] Đồng bộ lại Batch (Phòng trường hợp sửa thông tin Header ảnh hưởng logic, hoặc trigger lại)
        # Lưu ý: Logic update details phức tạp (thêm/xóa/sửa list) nên được xử lý ở các hàm detail riêng hoặc logic merge.
        # Ở đây ta gọi sync để đảm bảo các detail hiện có đều có batch.
        self._sync_batches_from_receipt(db_obj)

        return db_obj

    def delete(self, receipt_id: int):
        db_obj = self.get(receipt_id)
        if not db_obj:
            raise HTTPException(status_code=404, detail="Phiếu nhập không tồn tại.")
        
        receipt: MaterialReceipt = db_obj

        # 1. Revert PO Quantity & Status
        if receipt.po_header_id:
            detail: MaterialReceiptDetail 
            for detail in receipt.details:
                self._update_po_received_quantity(
                    po_id=receipt.po_header_id,
                    material_id=detail.material_id, 
                    quantity_delta_kg= -detail.received_quantity_kg 
                )
            self._check_and_close_po(receipt.po_header_id)

        # 2. Xóa các Batch liên quan (Nếu cần)
        # Tùy nghiệp vụ: Có thể xóa Batch hoặc để Batch mồ côi. 
        # Tốt nhất là set active=False hoặc xóa nếu batch chưa dùng.
        # Ở đây ta để Database Cascade (nếu config) hoặc xóa tay:
        for detail in receipt.details:
            batch = self.db.query(Batch).filter(Batch.receipt_detail_id == detail.detail_id).first()
            if batch:
                # Nếu batch chưa xuất kho/dùng -> xóa. Nếu dùng rồi -> lỗi Integrity
                try:
                    self.db.delete(batch)
                except:
                    pass # Bỏ qua nếu không xóa được batch

        self.db.delete(receipt)
        self.db.commit()
        return {"message": "Đã xóa phiếu nhập, cập nhật lại PO và xóa các lô hàng liên quan."}

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
        
        # 2. Update PO
        if receipt.po_header_id:
             self._check_and_close_po(receipt.po_header_id)

        self.db.commit()
        self.db.refresh(new_detail)

        # 3. [AUTO LINK] Tạo Batch cho dòng mới này
        self._sync_batch_for_detail(new_detail)

        return new_detail

    def update_detail(self, detail_id: int, obj_in: MaterialReceiptDetailUpdate) -> MaterialReceiptDetail:
        db_detail = self.get_detail(detail_id)
        if not db_detail:
            raise HTTPException(status_code=404, detail="Chi tiết phiếu nhập không tồn tại.")

        receipt_obj = db_detail.header 
        
        # 1. Tính delta số lượng để update PO
        qty_delta = 0.0
        if obj_in.received_quantity_kg is not None:
            qty_delta = obj_in.received_quantity_kg - db_detail.received_quantity_kg

        # 2. Update Detail
        update_data = obj_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_detail, field, value)

        self.db.add(db_detail)

        # 3. Update PO
        if receipt_obj:
            receipt: MaterialReceipt = receipt_obj
            if receipt.po_header_id and qty_delta != 0:
                self._update_po_received_quantity(
                    po_id=receipt.po_header_id,
                    material_id=db_detail.material_id,
                    quantity_delta_kg=qty_delta
                )
                self._check_and_close_po(receipt.po_header_id)

        self.db.commit()
        self.db.refresh(db_detail)

        # 4. [AUTO LINK] Cập nhật thông tin Batch (VD: Mã lô NCC thay đổi)
        self._sync_batch_for_detail(db_detail)

        return db_detail

    def delete_detail(self, detail_id: int):
        db_detail = self.get_detail(detail_id)
        if not db_detail:
            raise HTTPException(status_code=404, detail="Chi tiết phiếu nhập không tồn tại.")

        receipt_obj = db_detail.header
        
        # 1. Revert PO
        if receipt_obj:
            receipt: MaterialReceipt = receipt_obj
            if receipt.po_header_id:
                self._update_po_received_quantity(
                    po_id=receipt.po_header_id,
                    material_id=db_detail.material_id,
                    quantity_delta_kg= -db_detail.received_quantity_kg 
                )
                self._check_and_close_po(receipt.po_header_id)

        # 2. Xóa Batch liên quan
        batch = self.db.query(Batch).filter(Batch.receipt_detail_id == detail_id).first()
        if batch:
            try:
                self.db.delete(batch)
            except:
                # Nếu không xóa được (do ràng buộc), set inactive
                batch.is_active = False
                batch.receipt_detail_id = None # Ngắt liên kết
                self.db.add(batch)

        self.db.delete(db_detail)
        self.db.commit()
        return {"message": "Đã xóa chi tiết, cập nhật PO và xử lý Batch."}

    # =========================================================================
    # INTERNAL HELPERS (LOGIC NGHIỆP VỤ)
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
            origin_country=detail_in.origin_country,
            note=detail_in.note
        )
        self.db.add(db_detail)

        if po_id:
            self._update_po_received_quantity(
                po_id=po_id,
                material_id=detail_in.material_id,
                quantity_delta_kg=detail_in.received_quantity_kg
            )
        return db_detail

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
     # [MỚI] Hàm sinh số phiếu tự động: YYYY/MM-XXX
    def generate_next_receipt_number(self) -> str:
        now = datetime.now()
        # Format prefix: 2025/11-
        prefix = now.strftime("%Y/%m-") 
        
        # Tìm phiếu nhập cuối cùng trong tháng có format này
        last_receipt = self.db.query(MaterialReceipt.receipt_number)\
            .filter(MaterialReceipt.receipt_number.like(f"{prefix}%"))\
            .order_by(desc(MaterialReceipt.receipt_number))\
            .first()
        
        if not last_receipt:
            return f"{prefix}001"
        
        try:
            # Lấy phần đuôi XXX
            # last_receipt là tuple ('2025/11-001',)
            last_number_str = last_receipt[0]
            sequence_part = last_number_str.split('-')[-1]
            next_sequence = int(sequence_part) + 1
            return f"{prefix}{next_sequence:03d}"
        except (ValueError, IndexError):
            # Fallback nếu format cũ không đúng chuẩn
            return f"{prefix}001"

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

    # --- [MỚI] LOGIC TỰ ĐỘNG TẠO BATCH ---
    def _sync_batches_from_receipt(self, receipt: MaterialReceipt):
        """Duyệt qua tất cả details để đồng bộ Batch"""
        for detail in receipt.details:
            self._sync_batch_for_detail(detail)

    def _sync_batch_for_detail(self, detail: MaterialReceiptDetail):
        """
        Tạo hoặc cập nhật Batch dựa trên Receipt Detail.
        Khóa liên kết: receipt_detail_id
        """
        # Nếu không có mã lô nhà cung cấp, có thể dùng placeholder hoặc bỏ qua
        # Ở đây ta vẫn tạo để quản lý tồn kho theo detail ID
        supplier_batch = detail.supplier_batch_no if detail.supplier_batch_no else f"NO-BATCH-{detail.detail_id}"

        # 1. Tìm Batch đã liên kết
        existing_batch = self.db.query(Batch).filter(
            Batch.receipt_detail_id == detail.detail_id
        ).first()

        if existing_batch:
            # A. Update: Chỉ cập nhật các trường thông tin cơ bản nếu thay đổi
            # Không reset QC Status vì có thể KCS đã kiểm rồi
            is_changed = False
            if existing_batch.supplier_batch_no != supplier_batch:
                existing_batch.supplier_batch_no = supplier_batch
                is_changed = True
            
            if existing_batch.material_id != detail.material_id:
                existing_batch.material_id = detail.material_id
                is_changed = True

            if existing_batch.origin_country != detail.origin_country:
                existing_batch.origin_country = detail.origin_country
                is_changed = True
            
            if is_changed:
                self.db.add(existing_batch)
                self.db.commit()
        else:
            # B. Create New
            # Internal Code sẽ được BatchService tự sinh (VD: BAT-YYMMDD-XXXX)
            batch_in = BatchCreate(
                supplier_batch_no=supplier_batch,
                material_id=detail.material_id,
                # Các trường ngày tháng user sẽ update sau
                qc_status=BatchQCStatus.PENDING, 
                is_active=True,
                receipt_detail_id=detail.detail_id, # QUAN TRỌNG: Khóa liên kết
                origin_country=detail.origin_country # [MỚI] Sync Origin
            )
            # Gọi Batch Service để tận dụng logic sinh mã
            self.batch_service.create(batch_in)