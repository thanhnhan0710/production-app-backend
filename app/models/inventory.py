from sqlalchemy import Column, Integer, Float, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base

class InventoryStock(Base):
    __tablename__ = "inventory_stocks"

    id = Column(Integer, primary_key=True, index=True)
    
    # Tồn kho được định danh bởi bộ 3: Vật tư - Kho - Lô
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False)
    warehouse_id = Column(Integer, ForeignKey("warehouses.warehouse_id"), nullable=False)
    batch_id = Column(Integer, ForeignKey("batches.batch_id"), nullable=False)
    
    # Số lượng
    quantity_on_hand = Column(Float, default=0.0) # Tồn thực tế trong kho
    quantity_reserved = Column(Float, default=0.0) # Đã giữ chỗ cho đơn sản xuất (chưa xuất)
    
    # Tồn khả dụng = On Hand - Reserved
    # Cột này có thể tính toán, nhưng lưu DB để query cho nhanh nếu dữ liệu lớn

    last_updated = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Ràng buộc duy nhất: Một Lô hàng ở trong Một Kho chỉ có 1 dòng tồn kho
    __table_args__ = (
        UniqueConstraint('material_id', 'warehouse_id', 'batch_id', name='uix_stock_loc_batch'),
    )

    # Relationships
    material = relationship("Material")
    warehouse = relationship("Warehouse")
    batch = relationship("Batch")