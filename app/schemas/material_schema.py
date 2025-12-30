from pydantic import BaseModel
from datetime import date
from typing import Optional

class MaterialBase(BaseModel):
    material_name: str
    lot_code: Optional[str] = None
    import_date: date
    quantity: int
    unit_id: int
    imported_by: int
    note:Optional[str] = None

class MaterialCreate(MaterialBase):
    pass

class MaterialUpdate(BaseModel):
    material_name: Optional[str] = None
    lot_code: Optional[str] = None
    import_date: Optional[date] = None
    quantity: Optional[int] = None
    unit_id: Optional[int] = None
    imported_by: Optional[int] = None
    note:Optional[str] = None

class MaterialResponse(MaterialBase):
    material_id: int

    class Config:
        from_attributes = True  
