from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base

class BOMHeader(Base):
    __tablename__ = "bom_headers"

    bom_id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.product_id"), nullable=False)
    bom_code = Column(String(50), unique=True, index=True, nullable=False)
    bom_name = Column(String(150), nullable=True)
    
    # --- THÔNG SỐ KỸ THUẬT TỪ EXCEL ---
    width_behind_loom = Column(Float, comment="Width behind loom (mm/cm)")
    picks = Column(Integer, comment="Mật độ sợi ngang (Picks)")
    target_weight_gm = Column(Float, comment="Trọng lượng mục tiêu (80.1 g/m)")
    
    # Tỷ lệ chung cho toàn bộ BOM
    total_scrap_rate = Column(Float, default=0.0, comment="Tỷ lệ hao hụt tổng (F18)")
    total_shrinkage_rate = Column(Float, default=0.0, comment="Tỷ lệ co rút tổng (F19)")
    
    version = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    product = relationship("Product", back_populates="boms")
    bom_details = relationship("BOMDetail", back_populates="header", cascade="all, delete-orphan")