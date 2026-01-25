from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class Material(Base):
    __tablename__ = "materials"

    # 1. Các trường cơ bản
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    material_code = Column(String(50), unique=True, index=True, nullable=False)
    material_type = Column(String(100), nullable=True)

    # 2. Thông số kỹ thuật
    spec_denier = Column(String(50), nullable=True)
    spec_filament = Column(Integer, nullable=True)
    hs_code = Column(String(20), nullable=True)

    # 3. Quản lý kho
    min_stock_level = Column(Float, default=0.0)

    # 4. Khóa ngoại (Foreign Keys)
    # Lưu ý: Cả 2 đều trỏ về bảng units
    uom_base_id = Column(Integer, ForeignKey("units.unit_id"), nullable=False)
    uom_production_id = Column(Integer, ForeignKey("units.unit_id"), nullable=False)

    # 5. Relationships (QUAN TRỌNG: Phải có foreign_keys=[...])
    # Không dùng back_populates để tránh vòng lặp lỗi bên Unit
    uom_base = relationship("Unit", foreign_keys=[uom_base_id])
    uom_production = relationship("Unit", foreign_keys=[uom_production_id])