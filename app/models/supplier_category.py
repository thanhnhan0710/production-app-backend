from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship
from app.db.base_class import Base

# ==========================================
# BẢNG LOẠI NHÀ CUNG CẤP (Supplier Categories)
# ==========================================
class SupplierCategory(Base):
    __tablename__ = "supplier_categories"

    category_id = Column(Integer, primary_key=True, index=True)
    category_name = Column(String(100), nullable=False, unique=True, comment="VD: Nhà cung cấp sợi, Nhà cung cấp phụ tùng...")
    description = Column(Text, nullable=True)

    # Quan hệ 1-Nhiều: 1 Loại NCC có nhiều NCC
    # Sử dụng chuỗi "Supplier" để tránh lỗi import vòng (circular import)
    suppliers = relationship("Supplier", back_populates="category")