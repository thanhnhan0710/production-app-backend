from sqlalchemy.orm import Session
from sqlalchemy import or_
from fastapi import HTTPException
from typing import List, Optional

from app.models.warehouse import Warehouse
# Import model liên quan để check ràng buộc khi xóa
# Lưu ý: Import bên trong hàm hoặc dùng string reference nếu gặp lỗi circular import, 
# nhưng ở đây import model class thường an toàn.
from app.models.material_receipt import MaterialReceipt 

from app.schemas.warehouse_schema import WarehouseCreate, WarehouseUpdate

class WarehouseService:
    def __init__(self, db: Session):
        self.db = db

    def get(self, warehouse_id: int) -> Optional[Warehouse]:
        return self.db.query(Warehouse).filter(Warehouse.warehouse_id == warehouse_id).first()

    def get_multi(self, skip: int = 0, limit: int = 100, search: str = None) -> List[Warehouse]:
        query = self.db.query(Warehouse)
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Warehouse.warehouse_name.ilike(search_term),
                    Warehouse.location.ilike(search_term)
                )
            )
        return query.offset(skip).limit(limit).all()

    def create(self, obj_in: WarehouseCreate) -> Warehouse:
        if self.db.query(Warehouse).filter(Warehouse.warehouse_name == obj_in.warehouse_name).first():
            raise HTTPException(status_code=400, detail=f"Kho '{obj_in.warehouse_name}' đã tồn tại.")

        db_obj = Warehouse(
            warehouse_name=obj_in.warehouse_name,
            location=obj_in.location,
            description=obj_in.description
        )
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def update(self, warehouse_id: int, obj_in: WarehouseUpdate) -> Warehouse:
        db_obj = self.get(warehouse_id)
        if not db_obj:
            raise HTTPException(status_code=404, detail="Kho không tồn tại.")

        update_data = obj_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def delete(self, warehouse_id: int):
        db_obj = self.get(warehouse_id)
        if not db_obj:
            raise HTTPException(status_code=404, detail="Kho không tồn tại.")
        
        # Kiểm tra ràng buộc: Không xóa kho đã có phiếu nhập
        receipt_count = self.db.query(MaterialReceipt).filter(MaterialReceipt.warehouse_id == warehouse_id).count()
        if receipt_count > 0:
            raise HTTPException(status_code=400, detail="Không thể xóa kho đã có phiếu nhập phát sinh.")

        self.db.delete(db_obj)
        self.db.commit()
        return {"message": "Đã xóa kho thành công."}