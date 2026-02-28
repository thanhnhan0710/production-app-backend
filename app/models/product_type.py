from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class ProductType(Base):
    __tablename__ = "product_types"

    product_type_id = Column(Integer, primary_key=True, index=True)
    # Tên loại (VD: Dây đai an toàn, Dây đai công nghiệp)
    type_name = Column(String(100), nullable=False)
    description = Column(String(255), nullable=True)

    # Relationship 1-N tới bảng Products
    products = relationship("Product", back_populates="product_type")