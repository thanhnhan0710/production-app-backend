from pydantic import BaseModel, EmailStr
from typing import Optional

class SupplierBase(BaseModel):
    supplier_name: str
    email: EmailStr
    phone: Optional[str] = None
    address:Optional[str] = None
    note:Optional[str] = None

class SupplierCreate(SupplierBase):
    pass

class SupplierUpdate(BaseModel):
    supplier_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address:Optional[str] = None
    note:Optional[str] = None

class SupplierResponse(SupplierBase):
    supplier_id: int

    class Config:
        from_attributes = True