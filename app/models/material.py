from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class Material(Base):
    __tablename__ = "materials"

    # 1. Các trường cơ bản
    material_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    material_code = Column(String(50), unique=True, index=True, nullable=False)
    material_name = Column(String(200), nullable=False, index=True)

    # 2. Khóa ngoại (Phân loại & Nguồn gốc)
    type_id = Column(Integer, ForeignKey("material_types.type_id"), nullable=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.supplier_id"), nullable=True)

    # 3. Thông số kỹ thuật (Đặc thù cho Sợi)
    color = Column(String(50), nullable=True)
    dtex = Column(Integer, nullable=True)
    filament = Column(String(20), nullable=True)

    # 4. Quản lý kho & Quy cách
    min_stock_level = Column(Float, default=0.0)
    kg_per_bobbin = Column(Float, nullable=True)

    # 5. Thiết lập Relationship (Mối quan hệ)
    material_type = relationship("MaterialType", back_populates="materials")
    
    # Dùng backref để tự động tạo quan hệ ngược lại bên model Supplier mà không cần sửa file supplier.py
    supplier = relationship("Supplier", backref="materials")