from pydantic import BaseModel
from datetime import date
from typing import Optional, List

class ShiftBase(BaseModel):
    shift_name: str
    note: Optional[str] = None

class ShiftCreate(ShiftBase):
    pass

class ShiftUpdate(BaseModel):
    shift_name: Optional[str] = None
    note: Optional[str] = None

class ShiftResponse(ShiftBase):
    shift_id: int

    class Config:
        from_attributes = True
