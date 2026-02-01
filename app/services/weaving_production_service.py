from sqlalchemy.orm import Session, joinedload
from app.models.weaving_production import WeavingProduction
from app.schemas.weaving_production_schema import WeavingProductionCreate, WeavingProductionUpdate
from typing import List, Optional

class WeavingProductionService:
    def __init__(self, db: Session):
        self.db = db

    def get_multi(self, skip: int = 0, limit: int = 100) -> List[WeavingProduction]:
        """
        Lấy danh sách sản xuất dệt kèm theo thông tin chi tiết (Join bảng)
        """
        return (
            self.db.query(WeavingProduction)
            .options(
                joinedload(WeavingProduction.machine),
                joinedload(WeavingProduction.basket),
                joinedload(WeavingProduction.shift),
                joinedload(WeavingProduction.updated_by)
            )
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_id(self, production_id: int) -> Optional[WeavingProduction]:
        """
        Lấy chi tiết một bản ghi sản xuất theo ID
        """
        return (
            self.db.query(WeavingProduction)
            .options(
                joinedload(WeavingProduction.machine),
                joinedload(WeavingProduction.basket),
                joinedload(WeavingProduction.shift),
                joinedload(WeavingProduction.updated_by)
            )
            .filter(WeavingProduction.id == production_id)
            .first()
        )

    def create(self, obj_in: WeavingProductionCreate) -> WeavingProduction:
        """
        Tạo mới bản ghi sản xuất dệt
        """
        # Chuyển đổi Schema Pydantic sang Dictionary để insert vào DB
        db_obj = WeavingProduction(
            machine_id=obj_in.machine_id,
            line=obj_in.line,
            basket_id=obj_in.basket_id,
            shift_id=obj_in.shift_id,
            total_weight=obj_in.total_weight,
            run_waste=obj_in.run_waste,
            setup_waste=obj_in.setup_waste,
            updated_by_id=obj_in.updated_by_id
        )
        
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        
        # Sau khi refresh, ta cần load lại các relationship để Response Schema có đủ data
        return self.get_by_id(db_obj.id)

    def update(self, production_id: int, obj_in: WeavingProductionUpdate) -> Optional[WeavingProduction]:
        """
        Cập nhật bản ghi sản xuất
        """
        db_obj = self.get_by_id(production_id)
        if not db_obj:
            return None
        
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)

        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

