from pydantic import BaseModel
from typing import Optional

# Import các Schema danh mục
from app.schemas.machine_type_schema import MachineTypeResponse
from app.schemas.machine_status_schema import MachineStatusResponse
from app.schemas.area_schema import AreaResponse # [CẬP NHẬT]

class MachineBase(BaseModel):
    machine_name: str
    serial_number: Optional[str] = None
    
    machine_type_id: Optional[int] = None
    status_id: Optional[int] = None
    area_id: Optional[int] = None

    polymorphic_type: str 

    # --- Trường đặc thù Máy Dệt ---
    total_lines: Optional[int] = None
    speed: Optional[int] = None
    purpose: Optional[str] = None

    # --- Trường đặc thù Máy Nhuộm ---
    capacity_kg: Optional[float] = None
    max_temperature: Optional[float] = None

class MachineCreate(MachineBase):
    pass

class MachineUpdate(BaseModel):
    machine_name: Optional[str] = None
    serial_number: Optional[str] = None
    machine_type_id: Optional[int] = None
    status_id: Optional[int] = None
    area_id: Optional[int] = None
    
    total_lines: Optional[int] = None
    speed: Optional[int] = None
    purpose: Optional[str] = None
    
    capacity_kg: Optional[float] = None
    max_temperature: Optional[float] = None

class MachineResponse(MachineBase):
    machine_id: int
    
    machine_type: Optional[MachineTypeResponse] = None
    status: Optional[MachineStatusResponse] = None
    area: Optional[AreaResponse] = None # [CẬP NHẬT]

    class Config:
        from_attributes = True