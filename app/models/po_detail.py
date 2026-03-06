from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean, Date
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class PurchaseOrderDetail(Base):
    __tablename__ = "purchase_order_details"

    detail_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    po_id = Column(Integer, ForeignKey("purchase_order_headers.po_id"), nullable=False)
    material_id = Column(Integer, ForeignKey("materials.material_id"), nullable=False)
    
    # Thông tin tài chính & Khối lượng (Đã bỏ tỷ giá, mặc định dùng USD)
    currency = Column(String(10), default="USD")
    quantity_kg = Column(Float, nullable=False)
    quantity_rolls = Column(Integer, default=0)
    unit_price = Column(Float, nullable=False) # Đơn giá bằng USD
    line_total = Column(Float, default=0.0)    # Thành tiền bằng USD
    is_pricing_by_roll = Column(Boolean, default=False)
    ocean_freight = Column(Float, nullable=True) # O/F từ file Excel (Thường cũng bằng USD)

    # --- THÔNG TIN LOGISTICS & THEO DÕI GIAO HÀNG TỪNG PHẦN ---
    confirm_delivery = Column(String(50), nullable=True) # VD: W13 2025
    goods_readiness = Column(String(50), nullable=True)  # VD: Ready, 8-Jul, HOLD
    shipping_line = Column(String(100), nullable=True)   # VD: COSCO, JJ, MSK
    forwarder = Column(String(100), nullable=True)       # VD: QUANTERM, TP LOG
    
    etd = Column(Date, nullable=True) # Estimated Time of Departure
    eta = Column(Date, nullable=True) # Estimated Time of Arrival
    atd = Column(Date, nullable=True) # Actual Time of Departure
    booking_date = Column(Date, nullable=True) # Confirm booking date

    received_quantity = Column(Float, default=0.0)
    received_rolls = Column(Integer, default=0)

    header = relationship("PurchaseOrderHeader", back_populates="details")