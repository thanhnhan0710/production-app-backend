from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class Yarn(Base):
    __tablename__ = "yarns"

    yarn_id = Column(Integer, primary_key=True, index=True)
    yarn_name = Column(String(100), nullable=False)
    item_code = Column(String(100), unique=True, index=True, nullable=False)
    type = Column(String(100), nullable=True)
    color=Column(String(100), nullable=True)
    origin= Column(String(100), nullable=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.supplier_id"))
    note=Column(String(150), nullable=True)

    # Quan hệ n-1: Nhân viên thuộc về một phòng ban
    supplier = relationship("Supplier", back_populates="yarns")

    yarn_lots = relationship("YarnLot", back_populates="yarn")