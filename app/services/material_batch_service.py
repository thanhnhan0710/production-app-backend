from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional
from app.models.material_batch import MaterialBatch
from app.schemas.material_batch_schema import MaterialBatchCreate, MaterialBatchUpdate

class MaterialBatchService:
    def count_batches(self, db: Session) -> int:
        """Đếm tổng số Lô nguyên vật liệu"""
        return db.query(MaterialBatch).count()

    def get_batch(self, db: Session, batch_id: int) -> Optional[MaterialBatch]:
        return db.query(MaterialBatch).filter(MaterialBatch.batch_id == batch_id).first()

    def get_batch_by_code(self, db: Session, batch_code: str) -> Optional[MaterialBatch]:
        return db.query(MaterialBatch).filter(MaterialBatch.batch_code == batch_code).first()

    def get_batches(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        search: Optional[str] = None,
        material_id: Optional[int] = None,
        status: Optional[str] = None
    ) -> List[MaterialBatch]:
        query = db.query(MaterialBatch)
        
        if search:
            # Tìm kiếm theo mã Lô
            query = query.filter(MaterialBatch.batch_code.ilike(f"%{search}%"))
        if material_id:
            query = query.filter(MaterialBatch.material_id == material_id)
        if status:
            query = query.filter(MaterialBatch.status == status)
            
        return query.order_by(MaterialBatch.created_at.desc()).offset(skip).limit(limit).all()

    def create_batch(self, db: Session, obj_in: MaterialBatchCreate) -> MaterialBatch:
        db_obj = MaterialBatch(**obj_in.model_dump())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update_batch(self, db: Session, batch_id: int, obj_in: MaterialBatchUpdate) -> Optional[MaterialBatch]:
        db_obj = self.get_batch(db, batch_id)
        if not db_obj:
            return None
            
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
            
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def delete_batch(self, db: Session, batch_id: int) -> bool:
        db_obj = self.get_batch(db, batch_id)
        if not db_obj:
            return False
        db.delete(db_obj)
        db.commit()
        return True

    # ==========================================
    # LOGIC TỰ ĐỘNG SINH MÃ LÔ THEO YÊU CẦU
    # Định dạng: V + [Năm 2 số] + [Số thứ tự 4 số] (VD: V260001)
    # ==========================================
    def generate_batch_code(self, db: Session) -> str:
        current_year = datetime.now().strftime("%y") # Lấy 2 số cuối của năm (VD: '26')
        prefix = f"V{current_year}"

        # Tìm mã lô cuối cùng trong năm nay
        last_batch = db.query(MaterialBatch)\
            .filter(MaterialBatch.batch_code.like(f"{prefix}%"))\
            .order_by(MaterialBatch.batch_code.desc())\
            .first()

        if not last_batch:
            return f"{prefix}0001" # Nếu chưa có lô nào trong năm, bắt đầu là 0001

        # Cắt chuỗi để lấy phần số (VD: V260001 -> cắt từ index 3 lấy '0001')
        try:
            last_seq = int(last_batch.batch_code[3:])
            new_seq = last_seq + 1
        except ValueError:
            new_seq = 1

        # Trả về chuỗi mới, zfill(4) để luôn có 4 chữ số (0001, 0002...)
        return f"{prefix}{new_seq:04d}"

material_batch_service = MaterialBatchService()