from sqlalchemy import Column, Integer, String, Float, ForeignKey, Date, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base

class PurchaseOrderHeader(Base):
    __tablename__ = "purchase_orders"

    po_id = Column(Integer, primary_key=True, index=True)
    
    # Số PO (User nhập hoặc tự sinh, VD: PO-2024-001)
    po_number = Column(String(50), unique=True, index=True, nullable=False)
    
    vendor_id = Column(Integer, ForeignKey("suppliers.supplier_id"), nullable=False)
    
    order_date = Column(Date, default=func.now(),nullable=True) # Ngày đặt hàng
    expected_arrival_date = Column(Date, nullable=True) # Ngày ETA
    
    # --- ĐÃ THAY ĐỔI: Sử dụng Khóa ngoại thay cho Enum ---
    incoterm_id = Column(Integer, ForeignKey("incoterms.incoterm_id"), nullable=True)
    status_id = Column(Integer, ForeignKey("po_statuses.status_id"), nullable=True)
    
    # Tổng tiền hàng (Lưu ý: Do chi tiết có tỷ giá riêng, cột này thường lưu tổng tiền quy đổi VND)
    total_amount = Column(Float, default=0.0) 
    note = Column(String(255), nullable=True)

    created_at = Column(DateTime, server_default=func.now(), nullable=True)
    updated_at = Column(DateTime, onupdate=func.now(), nullable=True)

    # --- Relationships ---
    vendor = relationship("Supplier")
    incoterm = relationship("Incoterm")   # Trỏ đến bảng Incoterm
    status = relationship("POStatus")     # Trỏ đến bảng POStatus
    
    details = relationship("PurchaseOrderDetail", back_populates="header", cascade="all, delete-orphan")