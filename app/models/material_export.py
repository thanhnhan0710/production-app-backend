from sqlalchemy import Column, Integer, String, Float, ForeignKey, Date, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base

# Bảng Header: Phiếu xuất kho
class MaterialExport(Base):
    __tablename__ = "material_exports"

    id = Column(Integer, primary_key=True, index=True)
    export_code = Column(String(50), unique=True, index=True, nullable=False) # VD: PX-2024-001
    export_date = Column(Date, default=func.now())
    
    # 1. Xuất từ kho nào
    warehouse_id = Column(Integer, ForeignKey("warehouses.warehouse_id"), nullable=False)
    
    # 2. Xuất cho ai (Người nhận sẽ là người Đứng máy/Vào rổ)
    receiver_id = Column(Integer, ForeignKey("employees.employee_id"), nullable=True) 
    department_id = Column(Integer, ForeignKey("departments.department_id"), nullable=True)
    
    # 3. Ca làm việc
    shift_id = Column(Integer, ForeignKey("shifts.shift_id"), nullable=True)
    
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    created_by = Column(String(50), nullable=True)

    # Relationships
    warehouse = relationship("Warehouse")
    receiver = relationship("Employee")
    department = relationship("Department")
    shift = relationship("Shift")
    
    details = relationship("MaterialExportDetail", back_populates="header", cascade="all, delete-orphan")

# Bảng Detail: Chi tiết xuất & Thông tin đích đến
class MaterialExportDetail(Base):
    __tablename__ = "material_export_details"

    detail_id = Column(Integer, primary_key=True, index=True)
    export_id = Column(Integer, ForeignKey("material_exports.id"), nullable=False)
    
    # --- THÔNG TIN KHO (Để trừ tồn kho) ---
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False)
    batch_id = Column(Integer, ForeignKey("batches.batch_id"), nullable=False) # Lô sợi xuất đi
    quantity = Column(Float, nullable=False) # Số lượng xuất (Kg)
    
    # --- THÔNG TIN SẢN XUẤT (Để tạo Phiếu rổ tự động) ---
    # Xuất cho máy nào, line nào?
    machine_id = Column(Integer, ForeignKey("machines.machine_id"), nullable=True)
    machine_line = Column(Integer, nullable=True) # Line 1 hoặc Line 2 (Quan trọng)
    
    # Làm sản phẩm gì, tiêu chuẩn nào, bỏ vào rổ nào?
    product_id = Column(Integer, ForeignKey("products.product_id"), nullable=True)
    standard_id = Column(Integer, ForeignKey("standards.standard_id"), nullable=True)
    basket_id = Column(Integer, ForeignKey("baskets.basket_id"), nullable=True)
    
    note = Column(String(200), nullable=True)

    # Relationships
    header = relationship("MaterialExport", back_populates="details")
    material = relationship("Material")
    batch = relationship("Batch")
    machine = relationship("Machine")
    product = relationship("Product")
    basket = relationship("Basket")