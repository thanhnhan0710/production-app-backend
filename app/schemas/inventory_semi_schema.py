from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum

# Import Enum từ Model (hoặc định nghĩa lại nếu cần)
from app.models.inventory_semi import ExportReason, StockStatus

# =======================
# SHARED / NESTED SCHEMAS
# =======================
class WeavingTicketShort(BaseModel):
    id: int
    code: str
    class Config:
        from_attributes = True

class EmployeeShort(BaseModel):
    employee_id: int
    # full_name: str
    class Config:
        from_attributes = True

# =======================================================
# 1. IMPORT SCHEMAS (NHẬP KHO)
# =======================================================

class ImportDetailBase(BaseModel):
    weaving_ticket_id: int = Field(..., description="ID của phiếu rổ dệt (Item nhập)")
    warehouse_location: Optional[str] = Field(None, description="Vị trí lưu kho (Kệ A...)")
    note: Optional[str] = None

class ImportDetailCreate(ImportDetailBase):
    pass

class ImportDetailResponse(ImportDetailBase):
    id: int
    status: StockStatus
    weaving_ticket: Optional[WeavingTicketShort] = None
    class Config:
        from_attributes = True

# --- HEADER ---

class ImportTicketBase(BaseModel):
    code: str = Field(..., max_length=50)
    import_date: Optional[datetime] = None
    employee_id: int
    
class ImportTicketCreate(ImportTicketBase):
    details: List[ImportDetailCreate] # Danh sách chi tiết nhập

class ImportTicketResponse(ImportTicketBase):
    id: int
    details: List[ImportDetailResponse]
    employee: Optional[EmployeeShort] = None
    class Config:
        from_attributes = True


# =======================================================
# 2. EXPORT SCHEMAS (XUẤT KHO)
# =======================================================

class ExportDetailBase(BaseModel):
    weaving_ticket_id: int = Field(..., description="ID của phiếu rổ dệt cần xuất")
    note: Optional[str] = None

class ExportDetailCreate(ExportDetailBase):
    pass

class ExportDetailResponse(ExportDetailBase):
    id: int
    status: StockStatus
    weaving_ticket: Optional[WeavingTicketShort] = None
    class Config:
        from_attributes = True

# --- HEADER ---

class ExportTicketBase(BaseModel):
    code: str = Field(..., max_length=50)
    export_date: Optional[datetime] = None
    employee_id: int
    reason: ExportReason = Field(default=ExportReason.TO_DYEING)

class ExportTicketCreate(ExportTicketBase):
    details: List[ExportDetailCreate] # Danh sách chi tiết xuất

class ExportTicketResponse(ExportTicketBase):
    id: int
    details: List[ExportDetailResponse]
    employee: Optional[EmployeeShort] = None
    class Config:
        from_attributes = True