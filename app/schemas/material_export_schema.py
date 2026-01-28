from pydantic import BaseModel
from typing import Optional, List
from datetime import date

# Base Detail
class MaterialExportDetailBase(BaseModel):
    material_id: int
    batch_id: int
    quantity: float
    machine_id: Optional[int] = None
    machine_line: Optional[int] = None
    product_id: Optional[int] = None
    standard_id: Optional[int] = None
    basket_id: Optional[int] = None
    note: Optional[str] = None

class MaterialExportDetailCreate(MaterialExportDetailBase):
    pass

class MaterialExportDetailUpdate(BaseModel):
    # Cho phép update số lượng hoặc ghi chú. 
    # Hạn chế update Batch/Material vì ảnh hưởng kho nghiêm trọng.
    quantity: Optional[float] = None
    note: Optional[str] = None

class MaterialExportDetailResponse(MaterialExportDetailBase):
    detail_id: int
    # Có thể thêm nested info nếu cần (material name, etc)
    class Config:
        from_attributes = True

# Header Schemas
class MaterialExportBase(BaseModel):
    export_code: str
    export_date: Optional[date] = None
    warehouse_id: int
    department_id: Optional[int] = None
    receiver_id: int 
    shift_id: Optional[int] = None
    note: Optional[str] = None
    created_by: Optional[str] = None

class MaterialExportCreate(MaterialExportBase):
    details: List[MaterialExportDetailCreate]

class MaterialExportUpdate(BaseModel):
    export_date: Optional[date] = None
    department_id: Optional[int] = None
    receiver_id: Optional[int] = None
    shift_id: Optional[int] = None
    note: Optional[str] = None

class MaterialExportResponse(MaterialExportBase):
    id: int
    details: List[MaterialExportDetailResponse] = []
    class Config:
        from_attributes = True

# --- FILTER SCHEMA ---
class MaterialExportFilter(BaseModel):
    search: Optional[str] = None # Tìm theo Code, Note
    warehouse_id: Optional[int] = None
    receiver_id: Optional[int] = None
    from_date: Optional[date] = None
    to_date: Optional[date] = None