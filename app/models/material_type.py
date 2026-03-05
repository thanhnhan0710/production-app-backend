from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class MaterialType(Base):
    __tablename__ = "material_types"

    type_id = Column(Integer, primary_key=True, index=True)
    type_name = Column(String(100), nullable=False, unique=True, index=True, comment="VD: Sợi Polyester, Sợi Cotton, Hóa chất...")
    description = Column(Text, nullable=True)

    # Quan hệ 1-Nhiều: 1 Loại NVL có nhiều NVL
    materials = relationship("Material", back_populates="material_type")