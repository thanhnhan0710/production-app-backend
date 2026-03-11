from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date, datetime

# ==========================================
# CÁC SCHEMA PHỤ TRỢ CHO RESPONSE (HIỂN THỊ)
# ==========================================
class SimpleWarehouse(BaseModel):
    warehouse_id: int
    name: Optional[str] = None
    
    class Config:
        from_attributes = True

class SimpleEmployee(BaseModel):
    employee_id: int
    full_name: Optional[str] = None
    
    class Config:
        from_attributes = True

class SimpleMaterial(BaseModel):
    material_id: int
    material_code: str
    material_name: Optional[str] = None
    
    class Config:
        from_attributes = True

class SimpleBatch(BaseModel):
    batch_id: int
    batch_code: str
    supplier_batch_no: Optional[str] = None
    
    class Config:
        from_attributes = True

class SimpleLoomInfo(BaseModel):
    id: int
    machine_id: int
    line_number: int
    # Thông tin thêm sẽ được query và gán thủ công hoặc qua properties
    machine_name: Optional[str] = None
    product_code: Optional[str] = None

    class Config:
        from_attributes = True

# ==========================================
# SCHEMA CHO CHI TIẾT PHIẾU XUẤT (DETAIL)
# ==========================================
class MaterialExportDetailBase(BaseModel):
    material_id: int
    batch_id: int
    quantity_kg: float = Field(..., gt=0, description="Khối lượng xuất phải lớn hơn 0")
    quantity_cones: int = Field(default=0, ge=0)
    number_of_pallets: int = Field(default=0, ge=0)
    component_type: Optional[str] = Field(None, description="Loại sợi: GROUND, BINDER, PILE...")
    loom_id: Optional[int] = Field(None, description="ID của phiên chạy máy (MachineProductHistory) nhận hàng")
    note: Optional[str] = None

class MaterialExportDetailCreate(MaterialExportDetailBase):
    pass # Dùng khi tạo mới phiếu

class MaterialExportDetailResponse(MaterialExportDetailBase):
    detail_id: int
    export_id: int
    
    # Các object lồng nhau để Frontend dễ hiển thị
    material: Optional[SimpleMaterial] = None
    batch: Optional[SimpleBatch] = None
    # Nếu cần trả về chi tiết loom (tên máy, dòng máy)
    loom_info: Optional[SimpleLoomInfo] = None

    class Config:
        from_attributes = True

# ==========================================
# SCHEMA CHO PHIẾU XUẤT (HEADER)
# ==========================================
class MaterialExportBase(BaseModel):
    export_date: date
    warehouse_id: int
    exporter_id: Optional[int] = None
    receiver_id: Optional[int] = None
    department_id: Optional[int] = None
    shift_id: Optional[int] = None
    note: Optional[str] = None

class MaterialExportCreate(MaterialExportBase):
    # Cho phép truyền mảng các chi tiết xuất kho khi tạo phiếu
    details: List[MaterialExportDetailCreate] = Field(..., min_length=1, description="Phải có ít nhất 1 chi tiết xuất kho")

class MaterialExportUpdate(BaseModel):
    export_date: Optional[date] = None
    exporter_id: Optional[int] = None
    receiver_id: Optional[int] = None
    department_id: Optional[int] = None
    shift_id: Optional[int] = None
    note: Optional[str] = None
    # Lưu ý: Thường việc update số lượng/chi tiết sẽ làm thông qua API riêng cho Detail để đảm bảo tồn kho được đồng bộ đúng.

class MaterialExportResponse(MaterialExportBase):
    id: int
    export_code: str
    created_at: datetime
    created_by: Optional[str] = None
    
    # Nested relations
    warehouse: Optional[SimpleWarehouse] = None
    exporter: Optional[SimpleEmployee] = None
    receiver: Optional[SimpleEmployee] = None
    
    details: List[MaterialExportDetailResponse] = []

    class Config:
        from_attributes = True