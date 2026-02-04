from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from app.models.weaving_production import WeavingProduction
# Giả sử bạn có model Machine để join khi search
from app.models.machine import Machine 
from app.schemas.weaving_production_schema import WeavingProductionCreate, WeavingProductionUpdate
from typing import List, Optional

class WeavingProductionService:
    def __init__(self, db: Session):
        self.db = db

    # [CẬP NHẬT] Thêm tham số weaving_ticket_id vào đây
    def get_multi(
        self, 
        skip: int = 0, 
        limit: int = 100, 
        weaving_ticket_id: Optional[int] = None
    ) -> List[WeavingProduction]:
        """
        Lấy danh sách sản xuất, hỗ trợ lọc theo Ticket ID.
        """
        query = self.db.query(WeavingProduction).options(
            joinedload(WeavingProduction.machine),
            joinedload(WeavingProduction.basket),
            joinedload(WeavingProduction.shift),
            joinedload(WeavingProduction.updated_by)
        )

        # [LOGIC MỚI] Filter theo weaving_ticket_id nếu có
        # Lưu ý: Model WeavingProduction cần có cột weaving_ticket_id (hoặc logic join tương đương)
        if weaving_ticket_id:
            # Nếu trong DB bạn lưu basket_id nhưng muốn tìm theo ticket_id,
            # bạn có thể cần join với bảng WeavingTicket. 
            # Ở đây tôi giả định bảng WeavingProduction đã có cột weaving_ticket_id hoặc bạn muốn lọc trực tiếp.
            # Nếu chưa có cột này, hãy đảm bảo Model đã được cập nhật.
            if hasattr(WeavingProduction, 'weaving_ticket_id'):
                query = query.filter(WeavingProduction.weaving_ticket_id == weaving_ticket_id)
            else:
                # Fallback: Nếu không có cột ticket_id, có thể bạn muốn lọc theo basket_id của ticket đó?
                # Đoạn này tùy thuộc vào thiết kế DB của bạn.
                pass 

        return query.order_by(WeavingProduction.updated_at.desc()).offset(skip).limit(limit).all()

    def get_by_id(self, production_id: int) -> Optional[WeavingProduction]:
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
        # [LƯU Ý] Nếu Schema Create có weaving_ticket_id, hãy thêm vào đây
        db_obj = WeavingProduction(
            machine_id=obj_in.machine_id,
            line=obj_in.line,
            basket_id=obj_in.basket_id,
            shift_id=obj_in.shift_id,
            total_weight=obj_in.total_weight,
            run_waste=obj_in.run_waste,
            setup_waste=obj_in.setup_waste,
            updated_by_id=obj_in.updated_by_id,
            # weaving_ticket_id=obj_in.weaving_ticket_id # Bỏ comment nếu model có trường này
        )
        
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return self.get_by_id(db_obj.id) # Load lại relationship

    def update(self, production_id: int, obj_in: WeavingProductionUpdate) -> Optional[WeavingProduction]:
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

    # [BỔ SUNG] Hàm Delete
    def delete(self, production_id: int) -> bool:
        db_obj = self.db.query(WeavingProduction).filter(WeavingProduction.id == production_id).first()
        if not db_obj:
            return False
        self.db.delete(db_obj)
        self.db.commit()
        return True

    # [BỔ SUNG] Hàm Search
    def search(self, keyword: Optional[str], machine_id: Optional[int], skip: int = 0, limit: int = 100) -> List[WeavingProduction]:
        query = self.db.query(WeavingProduction).options(
            joinedload(WeavingProduction.machine),
            joinedload(WeavingProduction.basket),
            joinedload(WeavingProduction.shift),
            joinedload(WeavingProduction.updated_by)
        )

        if machine_id:
            query = query.filter(WeavingProduction.machine_id == machine_id)
        
        if keyword:
            # Tìm kiếm theo tên máy (cần join bảng machines)
            query = query.join(WeavingProduction.machine).filter(
                Machine.name.contains(keyword)
            )

        return query.order_by(WeavingProduction.updated_at.desc()).offset(skip).limit(limit).all()