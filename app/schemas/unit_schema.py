from pydantic import BaseModel
from typing import Optional

class UnitBase(BaseModel):
    unit_name: str
    note: Optional[str] = None

class UnitCreate(UnitBase):
    pass

class UnitUpdate(BaseModel):
    unit_name: Optional[str] = None

class UnitResponse(UnitBase):
    unit_id: int

    class Config:
        from_attributes = True  # Pydantic v2
