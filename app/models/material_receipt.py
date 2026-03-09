from sqlalchemy import Column, Integer, String, ForeignKey, Date, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base

class MaterialReceipt(Base):
    __tablename__ = "material_receipts"

    receipt_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Mã phiếu nhập
    receipt_number = Column(String(50), unique=True, index=True, nullable=False)
    receipt_date = Column(Date, default=func.now())
    
    # Liên kết 3 bên
    po_header_id = Column(Integer, ForeignKey("purchase_order_headers.po_id"), nullable=True)
    warehouse_id = Column(Integer, ForeignKey("warehouses.warehouse_id"), nullable=False)
    
    # Thông tin Logistics
    container_no = Column(String(50), nullable=True, comment="Số Container")
    seal_no = Column(String(50), nullable=True, comment="Số Seal (Chì)")
    
    # Trạng thái phiếu nhập (Draft: Đang tạo, Completed: Đã duyệt & Cộng tồn kho)
    status = Column(String(20), default="Draft", comment="Draft, Completed, Cancelled")
    
    note = Column(Text, nullable=True)
    created_by = Column(String(50), nullable=True)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    # Relationships
    warehouse = relationship("Warehouse")
    po_header = relationship("PurchaseOrderHeader")
    
    # Cascade: Xóa phiếu nhập cha thì tự động xóa các dòng chi tiết
    details = relationship("MaterialReceiptDetail", back_populates="header", cascade="all, delete-orphan")