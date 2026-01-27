from sqlalchemy.orm import Session
from sqlalchemy import or_, desc
from fastapi import HTTPException
from typing import List, Optional
from datetime import datetime

# Import Model và Schema
from app.models.batch import Batch, BatchQCStatus
from app.schemas.batch_schema import BatchCreate, BatchUpdate

class BatchService:
    def __init__(self, db: Session):
        self.db = db

    def get(self, batch_id: int) -> Optional[Batch]:
        return self.db.query(Batch).filter(Batch.batch_id == batch_id).first()

    def get_by_internal_code(self, code: str) -> Optional[Batch]:
        return self.db.query(Batch).filter(Batch.internal_batch_code == code).first()

    def get_multi(
        self, 
        skip: int = 0, 
        limit: int = 100, 
        search: str = None,
        material_id: int = None,
        qc_status: BatchQCStatus = None,
        supplier_batch: str = None,
        location: str = None # [UPDATED] Thêm tham số lọc theo vị trí
    ) -> List[Batch]:
        """
        Tìm kiếm nâng cao Lô:
        - search: Mã nội bộ
        - supplier_batch: Mã lô NCC
        - material_id: Lọc theo vật tư
        - qc_status: Lọc trạng thái
        - location: Lọc theo vị trí kho
        """
        query = self.db.query(Batch)

        if material_id:
            query = query.filter(Batch.material_id == material_id)
        
        if qc_status:
            query = query.filter(Batch.qc_status == qc_status)

        if supplier_batch:
            query = query.filter(Batch.supplier_batch_no.ilike(f"%{supplier_batch}%"))

        # [UPDATED] Lọc theo vị trí chính xác
        if location:
            query = query.filter(Batch.location == location)

        if search:
            query = query.filter(Batch.internal_batch_code.ilike(f"%{search}%"))

        # Sắp xếp mới nhất lên đầu
        return query.order_by(desc(Batch.created_at)).offset(skip).limit(limit).all()

    # Hàm sinh mã lô nội bộ tự động: V[YY]0001 (VD: V260001)
    def generate_next_batch_code(self) -> str:
        # 1. Lấy 2 số cuối của năm hiện tại (VD: 2026 -> "26")
        current_year = datetime.now().strftime("%y")
        prefix = f"V{current_year}" # VD: V26

        # 2. Tìm mã lô lớn nhất trong năm nay (Bắt đầu bằng V26...)
        last_batch = self.db.query(Batch)\
            .filter(Batch.internal_batch_code.like(f"{prefix}%"))\
            .order_by(desc(Batch.internal_batch_code))\
            .first()
        
        if not last_batch:
            # Chưa có lô nào trong năm nay, bắt đầu từ 0001
            return f"{prefix}0001"
        
        try:
            # Lấy mã hiện tại (VD: V260001)
            current_code = last_batch.internal_batch_code
            
            # Cắt bỏ phần prefix (V26) để lấy phần số thứ tự (0001)
            # len(prefix) = 3 (V + 2 số năm)
            sequence_part = current_code[len(prefix):] 
            
            # Tăng lên 1
            next_number = int(sequence_part) + 1
            
            # Format lại: Prefix + 4 chữ số (đệm số 0)
            # VD: V26 + 0002
            return f"{prefix}{next_number:04d}"
        except (ValueError, IndexError):
            # Trường hợp dữ liệu cũ không đúng format, return mã an toàn mặc định
            return f"{prefix}0001"

    def create(self, obj_in: BatchCreate) -> Batch:
        # 1. Sinh mã lô nội bộ nếu chưa có
        internal_code = obj_in.internal_batch_code
        if not internal_code:
            internal_code = self.generate_next_batch_code()

        # 2. Kiểm tra trùng mã nội bộ (Double check)
        if self.get_by_internal_code(internal_code):
             # Nếu trùng (do race condition), thử sinh lại hoặc báo lỗi
             raise HTTPException(status_code=400, detail=f"Mã lô nội bộ {internal_code} đã tồn tại. Vui lòng thử lại.")

        # 3. Tạo object Batch
        db_obj = Batch(
            internal_batch_code=internal_code,
            supplier_batch_no=obj_in.supplier_batch_no,
            material_id=obj_in.material_id,
            
            manufacture_date=obj_in.manufacture_date,
            expiry_date=obj_in.expiry_date,
            origin_country=obj_in.origin_country,
            
            # [UPDATED] Thêm location vào quá trình tạo
            location=obj_in.location,

            receipt_detail_id=obj_in.receipt_detail_id,
            
            qc_status=obj_in.qc_status,
            qc_note=obj_in.qc_note,
            note=obj_in.note,
            is_active=obj_in.is_active
        )
        
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def update(self, db_obj: Batch, obj_in: BatchUpdate) -> Batch:
        # Note: Hàm này sử dụng cơ chế dynamic attribute setting
        # Vì BatchUpdate schema đã có trường 'location', nên obj_in.dict() sẽ tự động chứa nó
        # và vòng lặp for bên dưới sẽ tự động update location vào db_obj.
        # Không cần sửa code ở đây.
        update_data = obj_in.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def update_qc_status(self, batch_id: int, status: BatchQCStatus, note: str = None) -> Batch:
        batch = self.get(batch_id)
        if not batch:
            raise HTTPException(status_code=404, detail="Không tìm thấy lô hàng.")
        
        batch.qc_status = status
        if note:
            batch.qc_note = note
            
        self.db.add(batch)
        self.db.commit()
        self.db.refresh(batch)
        return batch

    def delete(self, batch_id: int) -> Batch:
        batch = self.get(batch_id)
        if not batch:
            raise HTTPException(status_code=404, detail="Không tìm thấy lô hàng cần xóa.")

        if batch.qc_status == BatchQCStatus.PASS:
             raise HTTPException(status_code=400, detail="Không thể xóa lô đã đạt chuẩn (Pass). Hãy dùng chức năng hủy (Deactivate).")

        self.db.delete(batch)
        self.db.commit()
        return batch