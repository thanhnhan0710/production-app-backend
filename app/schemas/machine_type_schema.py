from pydantic import BaseModel
from typing import Optional

class MachineTypeBase(BaseModel):
    type_name: str
    description: Optional[str] = None

class MachineTypeCreate(MachineTypeBase):
    pass

class MachineTypeUpdate(BaseModel):
    type_name: Optional[str] = None
    description: Optional[str] = None

class MachineTypeResponse(MachineTypeBase):
    machine_type_id: int

    class Config:
        from_attributes = True