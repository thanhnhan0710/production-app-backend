from pydantic import BaseModel
from typing import Optional, List
from datetime import date
from enum import Enum

# Import các Schema khác để lồng dữ liệu (Nested)
# Lưu ý: Đảm bảo bạn đã có các file schema này
from app.schemas.material_schema import MaterialResponse 
from app.schemas.unit_schema import UnitResponse 
from app.schemas.supplier_schema import SupplierResponse

# Import Enums
class IncotermType(str, Enum):
    EXW = "EXW"
    FOB = "FOB"
    CIF = "CIF"
    DDP = "DDP"
    DAP = "DAP"

class POStatus(str, Enum):
    DRAFT = "Draft"
    SENT = "Sent"
    CONFIRMED = "Confirmed"
    PARTIAL = "Partial"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"

# --- DETAIL SCHEMAS ---
class PODetailBase(BaseModel):
    material_id: int
    quantity: float
    unit_price: float
    uom_id: Optional[int] = None

class PODetailCreate(PODetailBase):
    pass

class PODetailUpdate(BaseModel):
    material_id: Optional[int] = None
    quantity: Optional[float] = None
    unit_price: Optional[float] = None
    uom_id: Optional[int] = None

class PODetailResponse(PODetailBase):
    detail_id: int
    line_total: float
    received_quantity: float
    
    # [QUAN TRỌNG] Thêm các trường này để hiển thị tên
    material: Optional[MaterialResponse] = None
    uom: Optional[UnitResponse] = None
    
    class Config:
        from_attributes = True

# --- HEADER SCHEMAS ---
class POHeaderBase(BaseModel):
    po_number: str
    vendor_id: int
    order_date: Optional[date] = None
    expected_arrival_date: Optional[date] = None
    incoterm: Optional[IncotermType] = IncotermType.EXW
    currency: Optional[str] = "VND"
    exchange_rate: Optional[float] = 1.0
    status: Optional[POStatus] = POStatus.DRAFT
    note: Optional[str] = None

class POHeaderCreate(POHeaderBase):
    details: List[PODetailCreate] = []

class POHeaderUpdate(BaseModel):
    po_number: Optional[str] = None
    vendor_id: Optional[int] = None
    order_date: Optional[date] = None
    expected_arrival_date: Optional[date] = None
    incoterm: Optional[IncotermType] = None
    currency: Optional[str] = None
    exchange_rate: Optional[float] = None
    status: Optional[POStatus] = None
    note: Optional[str] = None

class POHeaderResponse(POHeaderBase):
    po_id: int
    total_amount: float
    
    # [QUAN TRỌNG] Thêm trường vendor để hiển thị tên nhà cung cấp
    vendor: Optional[SupplierResponse] = None
    details: List[PODetailResponse] = []

    class Config:
        from_attributes = True