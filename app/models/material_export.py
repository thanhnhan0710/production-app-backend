from sqlalchemy import Column, Integer, String, Float, ForeignKey, Date, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base

# ==========================================
# BẢNG HEADER: Phiếu xuất kho
# ==========================================
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


# ==========================================
# BẢNG DETAIL: Chi tiết xuất kho cho từng Loom
# ==========================================
class MaterialExportDetail(Base):
    __tablename__ = "material_export_details"

    detail_id = Column(Integer, primary_key=True, index=True)
    export_id = Column(Integer, ForeignKey("material_exports.id", ondelete="CASCADE"), nullable=False)
    
    # Thông tin lô sợi xuất đi
    material_id = Column(Integer, ForeignKey("materials.material_id"), nullable=False)
    batch_id = Column(Integer, ForeignKey("material_batches.batch_id"), nullable=False)
    
    # [CẬP NHẬT] Số lượng xuất thực tế
    quantity_kg = Column(Float, nullable=False, comment="Khối lượng xuất (Kg)")
    quantity_cones = Column(Integer, default=0, comment="Số cuộn xuất")
    number_of_pallets = Column(Integer, default=0, comment="Số pallet xuất")
    
    # Loại thành phần sợi (Ví dụ: GROUND, BINDER, FILLING...)
    component_type = Column(String(50), nullable=True) 

    # [CẬP NHẬT] Đích đến: Liên kết trực tiếp tới Loom đang chạy (MachineProductHistory)
    # Từ ID này có thể truy ra được Machine, Line và Product đang chạy.
    loom_id = Column(Integer, ForeignKey("machine_product_histories.id"), nullable=True, comment="ID của phiên chạy (Loom) nhận hàng")
    
    note = Column(String(200), nullable=True)

    # Relationships
    header = relationship("MaterialExport", back_populates="details")
    material = relationship("Material")
    batch = relationship("MaterialBatch") 
    
    # [MỚI] Quan hệ trỏ về bảng Lịch sử/Loom đang chạy
    loom = relationship("MachineProductHistory")