from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base

class Supplier(Base):
    __tablename__ = "suppliers"

    supplier_id = Column(Integer, primary_key=True, index=True)
    supplier_name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    phone = Column(String(20), nullable=True)
    address=Column(String(150), nullable=True)
    note=Column(String(150), nullable=True)

    # Quan hệ n-1: Nhân viên thuộc về một phòng ban
    yarns = relationship("Yarn", back_populates="supplier")