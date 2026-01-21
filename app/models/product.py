from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class Product(Base):
    __tablename__ = "products"

    product_id = Column(Integer, primary_key=True, index=True)
    item_code = Column(String(100), unique=True, nullable=False)
    note = Column(String(255), nullable=True)
    image_url = Column(String(255), nullable=True)

    # Relationships
    # Sử dụng string "BOMHeader" để tránh circular import
    boms = relationship("BOMHeader", back_populates="product")
    
    # Giả định bảng Standard nằm ở file khác
    standards = relationship("Standard", back_populates="product")