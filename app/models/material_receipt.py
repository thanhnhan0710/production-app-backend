from sqlalchemy import Column, Integer, String, Float, ForeignKey, Date, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base

# 1. Bảng Header: Phiếu nhập kho Nguyên vật liệu
class MaterialReceipt(Base):
    __tablename__ = "material_receipts"

    receipt_id = Column(Integer, primary_key=True, index=True)
    
    # Mã phiếu nhập
    receipt_number = Column(String(50), unique=True, index=True, nullable=False)
    receipt_date = Column(Date, default=func.now())
    
    # Liên kết 3 bên
    po_header_id = Column(Integer, ForeignKey("purchase_orders.po_id"), nullable=True)
    declaration_id = Column(Integer, ForeignKey("import_declarations.id"), nullable=True)
    warehouse_id = Column(Integer, ForeignKey("warehouses.warehouse_id"), nullable=False)
    
    # Thông tin Logistics
    container_no = Column(String(50), nullable=True, comment="Số Container")
    seal_no = Column(String(50), nullable=True, comment="Số Seal (Chì)")
    
    note = Column(Text, nullable=True)
    created_by = Column(String(50), nullable=True)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    # Relationships
    warehouse = relationship("Warehouse")
    po_header = relationship("PurchaseOrderHeader")
    declaration = relationship("ImportDeclaration")
    
    details = relationship("MaterialReceiptDetail", back_populates="header", cascade="all, delete-orphan")

# 2. Bảng Detail: Chi tiết nhập kho
class MaterialReceiptDetail(Base):
    __tablename__ = "material_receipt_details"

    detail_id = Column(Integer, primary_key=True, index=True)
    
    receipt_id = Column(Integer, ForeignKey("material_receipts.receipt_id"), nullable=False)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False)
    
    # Số lượng PO (Tham khảo)
    po_quantity_kg = Column(Float, default=0.0, comment="SL Kg trên chứng từ")
    po_quantity_cones = Column(Integer, default=0, comment="SL Cuộn trên chứng từ")
    
    # Số lượng thực nhận
    received_quantity_kg = Column(Float, nullable=False, comment="SL Kg thực nhập")
    received_quantity_cones = Column(Integer, default=0, comment="SL Cuộn thực nhập")
    
    # Đóng gói
    number_of_pallets = Column(Integer, default=0, comment="Tổng số Pallet/Kiện hàng")

    supplier_batch_no = Column(String(100), nullable=True)
    
    # Nguồn gốc xuất xứ (để đồng bộ sang Batch)
    origin_country = Column(String(50), nullable=True)

    # [MỚI] Thêm cột Location (Vị trí kho) - Max 20 ký tự cho thoải mái (dù yêu cầu Batch là 10)
    location = Column(String(20), nullable=True, comment="Vị trí kho chi tiết (Bin Code)")

    note = Column(String(200), nullable=True)

    # Relationships
    header = relationship("MaterialReceipt", back_populates="details")
    material = relationship("Material")