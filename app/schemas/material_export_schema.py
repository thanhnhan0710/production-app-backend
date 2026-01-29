from pydantic import BaseModel
from typing import Optional, List
from datetime import date

# Base Detail (Giữ nguyên)
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
    quantity: Optional[float] = None
    note: Optional[str] = None

class MaterialExportDetailResponse(MaterialExportDetailBase):
    detail_id: int
    class Config:
        from_attributes = True

# Header Schemas
class MaterialExportBase(BaseModel):
    export_code: str
    export_date: Optional[date] = None
    warehouse_id: int
    department_id: Optional[int] = None
    exporter_id: Optional[int] = None  # (MỚI) Người xuất kho
    receiver_id: int 
    shift_id: Optional[int] = None
    note: Optional[str] = None
    created_by: Optional[str] = None

class MaterialExportCreate(MaterialExportBase):
    details: List[MaterialExportDetailCreate]

class MaterialExportUpdate(BaseModel):
    export_date: Optional[date] = None
    department_id: Optional[int] = None
    exporter_id: Optional[int] = None # (MỚI)
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
    search: Optional[str] = None
    warehouse_id: Optional[int] = None
    exporter_id: Optional[int] = None # (MỚI)
    receiver_id: Optional[int] = None
    from_date: Optional[date] = None
    to_date: Optional[date] = None