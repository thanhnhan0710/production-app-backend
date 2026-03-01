from pydantic import BaseModel
from typing import Optional

class MachineStatusBase(BaseModel):
    status_name: str
    color_code: Optional[str] = None
    description: Optional[str] = None

class MachineStatusCreate(MachineStatusBase):
    pass

class MachineStatusUpdate(BaseModel):
    status_name: Optional[str] = None
    color_code: Optional[str] = None
    description: Optional[str] = None

class MachineStatusResponse(MachineStatusBase):
    status_id: int

    class Config:
        from_attributes = True