from sqlalchemy import Column, Integer, String, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base_class import Base

# ==========================================
# BẢNG NHÀ CUNG CẤP (Suppliers)
# ==========================================
class Supplier(Base):
    __tablename__ = "suppliers"

    supplier_id = Column(Integer, primary_key=True, index=True)
    supplier_name = Column(String(255), nullable=False)
    short_name = Column(String(50), nullable=True)
    address = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)

    # Khóa ngoại liên kết đến bảng Loại nhà cung cấp
    category_id = Column(Integer, ForeignKey("supplier_categories.category_id"), nullable=True)

    # Quan hệ ngược lại (Nhiều NCC thuộc 1 Loại)
    # Sử dụng chuỗi "SupplierCategory" để tránh lỗi import vòng
    category = relationship("SupplierCategory", back_populates="suppliers")