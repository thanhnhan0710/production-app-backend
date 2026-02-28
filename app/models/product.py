from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class Product(Base):
    __tablename__ = "products"

    product_id = Column(Integer, primary_key=True, index=True)
    item_code = Column(String(100), unique=True, nullable=False)
    
    # Khóa ngoại liên kết tới bảng product_types
    product_type_id = Column(Integer, ForeignKey("product_types.product_type_id"), nullable=True)
    
    note = Column(String(255), nullable=True)
    image_url = Column(String(255), nullable=True)

    # Relationships
    # Liên kết với bảng ProductType để lấy thông tin loại sản phẩm
    product_type = relationship("ProductType", back_populates="products")
    
    # Sử dụng chuỗi để tránh lỗi import vòng (circular import)
    boms = relationship("BOMHeader", back_populates="product")
    standards = relationship("Standard", back_populates="product")