from pydantic import BaseModel
from typing import Optional, List
from datetime import date
from enum import Enum

# Import Enum để validate
class ImportType(str, Enum):
    E31 = "E31"
    E21 = "E21"
    A11 = "A11"
    A12 = "A12"
    G11 = "G11"

# --- DETAIL SCHEMAS ---
class ImportDetailBase(BaseModel):
    material_id: int
    quantity: float
    unit_price: float
    hs_code_actual: Optional[str] = None
    po_detail_id: Optional[int] = None

class ImportDetailCreate(ImportDetailBase):
    pass

class ImportDetailUpdate(BaseModel):
    material_id: Optional[int] = None
    quantity: Optional[float] = None
    unit_price: Optional[float] = None
    hs_code_actual: Optional[str] = None
    po_detail_id: Optional[int] = None

class ImportDetailResponse(ImportDetailBase):
    detail_id: int
    
    class Config:
        from_attributes = True

# --- HEADER SCHEMAS ---
class ImportDeclarationBase(BaseModel):
    declaration_no: str
    declaration_date: date
    type_of_import: ImportType
    bill_of_lading: Optional[str] = None
    invoice_no: Optional[str] = None
    total_tax_amount: Optional[float] = 0.0
    note: Optional[str] = None

class ImportDeclarationCreate(ImportDeclarationBase):
    # Cho phép tạo Header kèm chi tiết
    details: List[ImportDetailCreate] = []

class ImportDeclarationUpdate(BaseModel):
    declaration_no: Optional[str] = None
    declaration_date: Optional[date] = None
    type_of_import: Optional[ImportType] = None
    bill_of_lading: Optional[str] = None
    invoice_no: Optional[str] = None
    total_tax_amount: Optional[float] = None
    note: Optional[str] = None

class ImportDeclarationResponse(ImportDeclarationBase):
    id: int
    details: List[ImportDetailResponse] = []

    class Config:
        from_attributes = True