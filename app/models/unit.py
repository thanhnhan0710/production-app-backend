from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.db.base import Base

class Unit(Base):
    __tablename__ = "units"

    unit_id = Column(Integer, primary_key=True, index=True)
    unit_name = Column(String(50), nullable=False, unique=True)
    note= Column(String(150), nullable=True)

    # Quan hệ 1-n: Một đơn vị tính dùng cho nhiều vật tư
    materials = relationship("Material", back_populates="unit")
