from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.material_inventory import MaterialInventory
from app.schemas.material_inventory_schema import MaterialInventoryCreate, MaterialInventoryUpdate

class MaterialInventoryService:
    def count_inventories(self, db: Session) -> int:
        """Đếm tổng số bản ghi tồn kho"""
        return db.query(MaterialInventory).count()

    def get_inventory(self, db: Session, inventory_id: int) -> Optional[MaterialInventory]:
        return db.query(MaterialInventory).filter(MaterialInventory.inventory_id == inventory_id).first()

    def get_inventories(
        self, 
        db: Session, 
        warehouse_id: Optional[int] = None, 
        material_id: Optional[int] = None, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[MaterialInventory]:
        query = db.query(MaterialInventory)
        
        # Thêm các bộ lọc nếu có truyền từ Endpoint
        if warehouse_id:
            query = query.filter(MaterialInventory.warehouse_id == warehouse_id)
        if material_id:
            query = query.filter(MaterialInventory.material_id == material_id)
            
        return query.order_by(MaterialInventory.updated_at.desc()).offset(skip).limit(limit).all()

    def create_inventory(self, db: Session, obj_in: MaterialInventoryCreate) -> MaterialInventory:
        """Khởi tạo tồn kho thủ công (Dùng cho kiểm kê đầu kỳ)"""
        db_obj = MaterialInventory(**obj_in.model_dump())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update_inventory(self, db: Session, inventory_id: int, obj_in: MaterialInventoryUpdate) -> Optional[MaterialInventory]:
        db_obj = self.get_inventory(db, inventory_id)
        if not db_obj:
            return None
            
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
            
        db.commit()
        db.refresh(db_obj)
        return db_obj

    # ==========================================
    # LOGIC CỘNG TỒN KHO THÔNG MINH (DÙNG KHI NHẬP KHO)
    # Tự tìm dòng tồn kho (Kho + Vật tư + Lô + Vị trí), nếu có thì cộng dồn, chưa có thì tạo mới
    # ==========================================
    def add_stock(
        self, 
        db: Session, 
        warehouse_id: int, 
        material_id: int, 
        batch_id: int, 
        location: str, 
        qty_kg: float, 
        qty_cones: int
    ) -> MaterialInventory:
        loc_str = location if location else "N/A"
        
        # Tìm xem đã có dòng record nào khớp hoàn toàn 4 tiêu chí này chưa
        inventory = db.query(MaterialInventory).filter(
            MaterialInventory.warehouse_id == warehouse_id,
            MaterialInventory.material_id == material_id,
            MaterialInventory.batch_id == batch_id,
            MaterialInventory.location == loc_str
        ).first()

        if inventory:
            # Nếu có, cộng dồn số lượng
            inventory.quantity_kg += qty_kg
            inventory.quantity_cones += qty_cones
        else:
            # Nếu chưa, tạo dòng tồn kho mới
            inventory = MaterialInventory(
                warehouse_id=warehouse_id,
                material_id=material_id,
                batch_id=batch_id,
                location=loc_str,
                quantity_kg=qty_kg,
                quantity_cones=qty_cones
            )
            db.add(inventory)
            
        # Không dùng commit ở đây mà dùng flush để Transaction cha (Receipt) quản lý việc commit toàn cục
        db.flush() 
        return inventory

material_inventory_service = MaterialInventoryService()