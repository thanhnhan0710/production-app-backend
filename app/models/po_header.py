from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base_class import Base

class PurchaseOrderHeader(Base):
    __tablename__ = "purchase_order_headers"

    po_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    po_number = Column(String(50), unique=True, index=True, nullable=False)
    vendor_id = Column(Integer, ForeignKey("suppliers.supplier_id"), nullable=False)
    
    order_date = Column(DateTime, nullable=True)
    # ĐÃ XÓA: expected_arrival_date (Đã chuyển xuống Detail)
    
    incoterm_id = Column(Integer, ForeignKey("incoterms.incoterm_id"), nullable=True)
    status_id = Column(Integer, ForeignKey("po_statuses.status_id"), nullable=True)
    note = Column(Text, nullable=True)
    total_amount = Column(Float, default=0.0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    details = relationship("PurchaseOrderDetail", back_populates="header", cascade="all, delete-orphan")