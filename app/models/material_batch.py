from sqlalchemy import Column, Integer, String, Float, ForeignKey, Date, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base

class MaterialBatch(Base):
    __tablename__ = "material_batches"

    batch_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Mã lô nội bộ do hệ thống tự sinh (VD: V2603001)
    batch_code = Column(String(50), unique=True, index=True, nullable=False)
    
    # Liên kết với hàng hóa và nguồn gốc nhập (dòng chi tiết phiếu nhập)
    material_id = Column(Integer, ForeignKey("materials.material_id"), nullable=False)
    receipt_detail_id = Column(Integer, ForeignKey("material_receipt_details.detail_id"), nullable=True)

    # Thông tin truy xuất nguồn gốc (Kế thừa từ Phiếu nhập chi tiết)
    supplier_batch_no = Column(String(100), nullable=True, comment="Mã lô của Nhà cung cấp")
    origin_country = Column(String(50), nullable=True, comment="Quốc gia xuất xứ")
    manufacturing_date = Column(Date, nullable=True, comment="Ngày sản xuất")
    expiration_date = Column(Date, nullable=True, comment="Ngày hết hạn (Nếu có)")

    # Số lượng lúc mới khởi tạo (Lịch sử)
    initial_quantity_kg = Column(Float, default=0.0, comment="Tổng Kg ban đầu của lô")
    initial_quantity_cones = Column(Integer, default=0, comment="Tổng số cuộn ban đầu của lô")

    # Trạng thái lô hàng
    status = Column(String(20), default="Available", comment="Available, Quarantine, Blocked, Depleted")

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    # Relationships
    material = relationship("Material")
    receipt_detail = relationship("MaterialReceiptDetail")
    inventories = relationship("MaterialInventory", back_populates="batch")