from sqlalchemy.orm import Session
from sqlalchemy import desc
from fastapi import HTTPException
from typing import List, Optional

# Import Models
from app.models.iqc_result import IQCResult, IQCResultStatus
from app.models.batch import Batch, BatchQCStatus

# Import Schemas
from app.schemas.iqc_result_schema import IQCResultCreate, IQCResultUpdate

class IQCService:
    def __init__(self, db: Session):
        self.db = db

    def get(self, test_id: int) -> Optional[IQCResult]:
        return self.db.query(IQCResult).filter(IQCResult.test_id == test_id).first()

    def get_by_batch(self, batch_id: int) -> List[IQCResult]:
        """Lấy lịch sử kiểm tra của một lô hàng cụ thể"""
        return self.db.query(IQCResult)\
            .filter(IQCResult.batch_id == batch_id)\
            .order_by(desc(IQCResult.test_date))\
            .all()

    def get_multi(self, skip: int = 0, limit: int = 100) -> List[IQCResult]:
        return self.db.query(IQCResult)\
            .order_by(desc(IQCResult.test_date))\
            .offset(skip).limit(limit).all()

    def create(self, obj_in: IQCResultCreate) -> IQCResult:
        # 1. Kiểm tra Batch tồn tại
        batch = self.db.query(Batch).filter(Batch.batch_id == obj_in.batch_id).first()
        if not batch:
            raise HTTPException(status_code=404, detail="Lô hàng không tồn tại.")

        # 2. Tạo kết quả Test
        db_obj = IQCResult(
            batch_id=obj_in.batch_id,
            tester_name=obj_in.tester_name,
            tensile_strength=obj_in.tensile_strength,
            elongation=obj_in.elongation,
            color_fastness=obj_in.color_fastness,
            final_result=obj_in.final_result,
            note=obj_in.note
        )
        self.db.add(db_obj)
        # Flush để lấy ID nếu cần, nhưng chưa commit để đảm bảo tính toàn vẹn (Atomic Transaction)
        self.db.flush() 

        # 3. [QUAN TRỌNG] TỰ ĐỘNG KHÓA/MỞ BATCH
        # Nếu có kết quả Pass/Fail, cập nhật ngay vào bảng Batch để kho biết đường xuất/giữ
        self._sync_batch_status(batch, obj_in.final_result)
        
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def update(self, db_obj: IQCResult, obj_in: IQCResultUpdate) -> IQCResult:
        update_data = obj_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        self.db.add(db_obj)
        
        # 4. [QUAN TRỌNG] Đồng bộ lại trạng thái Batch nếu kết quả test thay đổi
        if obj_in.final_result:
            batch = self.db.query(Batch).get(db_obj.batch_id)
            if batch:
                self._sync_batch_status(batch, obj_in.final_result)

        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def _sync_batch_status(self, batch: Batch, iqc_status: IQCResultStatus):
        """
        Hàm nội bộ: Ánh xạ trạng thái từ kết quả IQC sang trạng thái của Lô hàng (Batch Master).
        - IQC Pass -> Batch Pass (Được phép xuất)
        - IQC Fail -> Batch Fail (Khóa, chờ xử lý)
        - IQC Pending -> Batch Pending
        """
        if iqc_status == IQCResultStatus.PASS:
            batch.qc_status = BatchQCStatus.PASS
            batch.qc_note = "IQC Passed: Auto updated by system"
        elif iqc_status == IQCResultStatus.FAIL:
            batch.qc_status = BatchQCStatus.FAIL
            batch.qc_note = "IQC Failed: Auto updated by system"
        else:
            batch.qc_status = BatchQCStatus.PENDING
        
        self.db.add(batch)