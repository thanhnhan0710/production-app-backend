from pydantic import BaseModel
from datetime import date
from typing import Optional, List

class MachineBase(BaseModel):
    machine_name: str
    total_lines: Optional[int] = None
    purpose: Optional[str] = None
    status: str

class MachineCreate(MachineBase):
    pass

class MachineUpdate(BaseModel):
    machine_name: Optional[str] = None
    total_lines: Optional[int] = None
    purpose: Optional[str] = None
    status: Optional[str] = None
    
class MachineResponse(MachineBase):
    machine_id: int

    class Config:
        from_attributes = True
