import enum
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Date, Enum, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base

# 1. Các Enum quan trọng cho xuất nhập khẩu
class IncotermType(str, enum.Enum):
    EXW = "EXW" # Giao tại xưởng (Người mua lo hết)
    FOB = "FOB" # Giao lên tàu (Phổ biến khi mua từ TQ/QT)
    CIF = "CIF" # Tiền hàng + Bảo hiểm + Cước (Phổ biến)
    DDP = "DDP" # Giao đã nộp thuế
    DAP = "DAP" # Giao tại nơi đến

class POStatus(str, enum.Enum):
    DRAFT = "Draft"         # Nháp
    SENT = "Sent"           # Đã gửi cho NCC
    CONFIRMED = "Confirmed" # NCC đã xác nhận
    PARTIAL = "Partial"     # Đã về một phần
    COMPLETED = "Completed" # Đã hoàn thành (Nhập kho đủ)
    CANCELLED = "Cancelled" # Hủy

# 2. Bảng Header (Thông tin chung đơn hàng)
class PurchaseOrderHeader(Base):
    __tablename__ = "purchase_orders"

    po_id = Column(Integer, primary_key=True, index=True)
    
    # Số PO (User nhập hoặc tự sinh, VD: PO-2024-001)
    po_number = Column(String(50), unique=True, index=True, nullable=False)
    
    vendor_id = Column(Integer, ForeignKey("suppliers.supplier_id"), nullable=False)
    
    order_date = Column(Date, default=func.now()) # Ngày đặt hàng
    expected_arrival_date = Column(Date, nullable=True) # Ngày ETA (Cực quan trọng cho nhập khẩu)
    
    incoterm = Column(Enum(IncotermType), default=IncotermType.EXW)
    currency = Column(String(10), default="VND") # VND, USD, CNY
    exchange_rate = Column(Float, default=1.0)   # Tỷ giá (nếu nhập khẩu)
    
    status = Column(Enum(POStatus), default=POStatus.DRAFT)
    
    total_amount = Column(Float, default=0.0) # Tổng tiền hàng (chưa VAT)
    note = Column(String(255), nullable=True)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    # Relationships
    vendor = relationship("Supplier")
    details = relationship("PurchaseOrderDetail", back_populates="header", cascade="all, delete-orphan")

# 3. Bảng Detail (Chi tiết các loại sợi mua)
class PurchaseOrderDetail(Base):
    __tablename__ = "purchase_order_details"

    detail_id = Column(Integer, primary_key=True, index=True)
    
    po_id = Column(Integer, ForeignKey("purchase_orders.po_id"), nullable=False)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False)
    
    quantity = Column(Float, nullable=False) # Số lượng mua
    unit_price = Column(Float, nullable=False) # Đơn giá
    
    # Đơn vị tính khi mua (Thường là Kg hoặc Pounds)
    uom_id = Column(Integer, ForeignKey("units.unit_id"), nullable=True) 
    
    line_total = Column(Float, default=0.0) # Thành tiền = SL * Đơn giá
    
    # Theo dõi nhập kho cho dòng này (để biết thiếu đủ)
    received_quantity = Column(Float, default=0.0) 

    # Relationships
    header = relationship("PurchaseOrderHeader", back_populates="details")
    material = relationship("Material")
    uom = relationship("Unit")