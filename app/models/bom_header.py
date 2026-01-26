# 1. Thêm import DECIMAL
from sqlalchemy import Column, Integer, Boolean, ForeignKey, DateTime, UniqueConstraint, DECIMAL
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base

class BOMHeader(Base):
    __tablename__ = "bom_headers"

    bom_id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.product_id"), nullable=False)
    
    # --- QUẢN LÝ THEO NĂM ---
    applicable_year = Column(Integer, nullable=False, comment="Năm áp dụng (VD: 2026)")

    # --- THÔNG SỐ KỸ THUẬT (Dùng DECIMAL(10, 2)) ---
    # Ví dụ: lưu 150.55
    width_behind_loom = Column(DECIMAL(10, 2), comment="Width behind loom (mm/cm)")
    
    picks = Column(Integer, comment="Mật độ sợi ngang (Picks)")
    
    # Ví dụ: lưu 80.12
    target_weight_gm = Column(DECIMAL(10, 2), comment="Trọng lượng mục tiêu (80.1 g/m)")
    
    # --- TỶ LỆ HAO HỤT (Dùng DECIMAL(10, 2)) ---
    # Ví dụ: lưu 1.50 hoặc 0.05
    total_scrap_rate = Column(DECIMAL(10, 2), default=0.00, comment="Tỷ lệ hao hụt tổng (F18)")
    
    total_shrinkage_rate = Column(DECIMAL(10, 2), default=0.00, comment="Tỷ lệ co rút tổng (F19)")
    
    # --- QUẢN LÝ PHIÊN BẢN & TRẠNG THÁI ---
    version = Column(Integer, default=1, comment="Phiên bản sửa đổi trong năm")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    # --- RELATIONSHIPS ---
    product = relationship("Product", back_populates="boms")
    bom_details = relationship("BOMDetail", back_populates="header", cascade="all, delete-orphan")

    # --- RÀNG BUỘC TOÀN VẸN ---
    __table_args__ = (
        # Lưu ý: UniqueConstraint này có nghĩa là mỗi Product chỉ có 1 BOM Header trong 1 năm.
        # Nếu bạn muốn lưu lịch sử nhiều Version, bạn nên thêm 'version' vào đây.
        # Ví dụ: UniqueConstraint('product_id', 'applicable_year', 'version', ...)
        UniqueConstraint('product_id', 'applicable_year', name='uq_bom_product_year'),
    )