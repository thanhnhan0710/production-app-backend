from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base

# 2. Bảng BOM Header (Quản lý phiên bản công thức)
class BOMHeader(Base):
    __tablename__ = "bom_headers"

    bom_id = Column(Integer, primary_key=True, index=True)
    
    # Liên kết với bảng Sản phẩm (Thành phẩm dây đai)
    # Lưu ý: Trỏ tới 'products.product_id' khớp với file product.py
    product_id = Column(Integer, ForeignKey("products.product_id"), nullable=False)
    
    bom_code = Column(String(50), unique=True, index=True, nullable=False) # VD: BOM-BELT-001-V1
    bom_name = Column(String(150), nullable=True) # VD: Công thức chuẩn 2024
    
    version = Column(Integer, default=1)
    is_active = Column(Boolean, default=True) # Chỉ có 1 BOM active cho 1 sản phẩm tại 1 thời điểm
    
    # Quy chuẩn sản xuất cho BOM này
    base_quantity = Column(Float, default=1.0) # Số lượng cơ sở (VD: Tính cho 1 mét dây hay 100 mét)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    # Relationships
    # Sử dụng string để lazy load và tránh circular imports
    product = relationship("Product", back_populates="boms")
    bom_details = relationship("BOMDetail", back_populates="header", cascade="all, delete-orphan")