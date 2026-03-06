from sqlalchemy import Boolean, Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class PurchaseOrderDetail(Base):
    __tablename__ = "purchase_order_details"

    detail_id = Column(Integer, primary_key=True, index=True)
    
    po_id = Column(Integer, ForeignKey("purchase_orders.po_id"), nullable=False)
    material_id = Column(Integer, ForeignKey("materials.material_id"), nullable=False)
    
    # --- ĐÃ CHUYỂN TỪ HEADER XUỐNG ĐÂY ---
    currency = Column(String(10), default="VND") # VND, USD, CNY
    exchange_rate = Column(Float, default=1.0)   # Tỷ giá (nếu nhập khẩu)
    
    quantity_kg = Column(Float, nullable=False) # Số lượng mua

    quantity_rolls = Column(Integer, default=0)
    
    # Đơn giá (Theo loại tiền tệ đang chọn ở dòng này)
    unit_price = Column(Float, nullable=False) 
    
    line_total = Column(Float, default=0.0) # Thành tiền = SL * Đơn giá (Theo ngoại tệ)
    is_pricing_by_roll = Column(Boolean, default=False)
    
    # Theo dõi nhập kho cho dòng này (để biết thiếu đủ)
    received_quantity = Column(Float, default=0.0)
    received_rolls = Column(Integer, default=0)     

    # --- Relationships ---
    header = relationship("PurchaseOrderHeader", back_populates="details")
    material = relationship("Material")