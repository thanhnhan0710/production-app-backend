from sqlalchemy import Column, Integer, String, Float, ForeignKey, Date, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base

# Bảng Header: Phiếu xuất kho (Giữ nguyên)
class MaterialExport(Base):
    __tablename__ = "material_exports"

    id = Column(Integer, primary_key=True, index=True)
    export_code = Column(String(50), unique=True, index=True, nullable=False)
    export_date = Column(Date, default=func.now())
    
    # 1. Xuất từ kho nào
    warehouse_id = Column(Integer, ForeignKey("warehouses.warehouse_id"), nullable=False)
    
    # 2. Người xuất kho
    exporter_id = Column(Integer, ForeignKey("employees.employee_id"), nullable=True)

    # 3. Xuất cho ai (Người nhận - Đứng máy)
    receiver_id = Column(Integer, ForeignKey("employees.employee_id"), nullable=True) 
    department_id = Column(Integer, ForeignKey("departments.department_id"), nullable=True)
    
    # 4. Ca làm việc
    shift_id = Column(Integer, ForeignKey("shifts.shift_id"), nullable=True)
    
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    created_by = Column(String(50), nullable=True)

    # Relationships
    warehouse = relationship("Warehouse")
    department = relationship("Department")
    shift = relationship("Shift")
    
    exporter = relationship("Employee", foreign_keys=[exporter_id])
    receiver = relationship("Employee", foreign_keys=[receiver_id])
    
    details = relationship("MaterialExportDetail", back_populates="header", cascade="all, delete-orphan")

# Bảng Detail: Chi tiết xuất (Cập nhật)
class MaterialExportDetail(Base):
    __tablename__ = "material_export_details"

    detail_id = Column(Integer, primary_key=True, index=True)
    export_id = Column(Integer, ForeignKey("material_exports.id"), nullable=False)
    
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False)
    batch_id = Column(Integer, ForeignKey("batches.batch_id"), nullable=False)
    quantity = Column(Float, nullable=False)
    
    # [NEW] Loại thành phần sợi (Lấy từ BOMComponentType: GROUND, BINDER, FILLING...)
    # Ví dụ: Batch A xuất 50kg làm sợi GROUND, Batch B xuất 10kg làm sợi BINDER
    component_type = Column(String(50), nullable=True) 

    # Thông tin sản xuất (Đích đến)
    machine_id = Column(Integer, ForeignKey("machines.machine_id"), nullable=True)
    machine_line = Column(Integer, nullable=True)
    
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