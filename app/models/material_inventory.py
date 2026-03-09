from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base

class MaterialInventory(Base):
    __tablename__ = "material_inventories"

    inventory_id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Không gian lưu trữ
    warehouse_id = Column(Integer, ForeignKey("warehouses.warehouse_id"), nullable=False)
    material_id = Column(Integer, ForeignKey("materials.material_id"), nullable=False)
    batch_id = Column(Integer, ForeignKey("material_batches.batch_id"), nullable=False)
    
    # Vị trí cụ thể trong kho (VD: A1-01, B2-05)
    location = Column(String(50), nullable=True, default="N/A", comment="Vị trí kho chi tiết")

    # Số lượng tồn kho khả dụng thực tế
    quantity_kg = Column(Float, default=0.0, nullable=False, comment="Số lượng Kg khả dụng")
    quantity_cones = Column(Integer, default=0, nullable=False, comment="Số lượng cuộn khả dụng")

    # Số lượng đang giữ chỗ (Dành cho việc đã lên lệnh Sản xuất nhưng chưa thực xuất)
    reserved_quantity_kg = Column(Float, default=0.0, comment="Số lượng Kg đã được giữ chỗ")
    reserved_quantity_cones = Column(Integer, default=0, comment="Số lượng cuộn đã được giữ chỗ")

    last_counted_date = Column(DateTime, nullable=True, comment="Ngày kiểm kê gần nhất")

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    # Ràng buộc BẮT BUỘC: Mỗi (Kho + Vật tư + Lô + Vị trí) chỉ có duy nhất 1 dòng Tồn kho.
    __table_args__ = (
        UniqueConstraint('warehouse_id', 'material_id', 'batch_id', 'location', name='_wh_mat_batch_loc_uc'),
    )

    # Relationships
    warehouse = relationship("Warehouse")
    material = relationship("Material")
    batch = relationship("MaterialBatch", back_populates="inventories")