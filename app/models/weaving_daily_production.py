from sqlalchemy import Column, Integer, Float, Date, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.base import Base

class WeavingDailyProduction(Base):
    __tablename__ = "weaving_daily_productions"

    id = Column(Integer, primary_key=True, index=True)
    
    # Ngày sản xuất (Lấy từ ngày ra rổ - time_out của phiếu dệt)
    date = Column(Date, nullable=False, index=True)
    
    # Sản phẩm
    product_id = Column(Integer, ForeignKey("products.product_id"), nullable=False)
    
    # Tổng số mét dệt được trong ngày của sp này
    total_meters = Column(Float, default=0.0)
    
    # Sản lượng (kg): Tổng số kg (Net Weight) dệt ra
    total_kg = Column(Float, default=0.0)
    
    # Tổng số line máy tham gia dệt sản phẩm này trong ngày
    # (Đếm số lượng machine_id + machine_line duy nhất)
    active_machine_lines = Column(Integer, default=0)

    # Relationships
    product = relationship("Product")

    # Constraint: Một ngày + một sản phẩm chỉ được có 1 dòng dữ liệu
    __table_args__ = (
        UniqueConstraint('date', 'product_id', name='uix_date_product'),
    )