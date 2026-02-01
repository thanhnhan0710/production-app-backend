from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# --- SCHEMAS BỔ TRỢ (Để lấy tên thay vì chỉ lấy ID) ---
class MachineShort(BaseModel):
    machine_id: int
    machine_name: str
    class Config:
        from_attributes = True

class BasketShort(BaseModel):
    basket_id: int
    basket_code: str 
    class Config:
        from_attributes = True

class ShiftShort(BaseModel):
    shift_id: int
    shift_name: str
    class Config:
        from_attributes = True

class EmployeeShoft(BaseModel):
    full_name: str
    class Config:
        from_attributes = True

# --- MAIN SCHEMAS ---

class WeavingProductionBase(BaseModel):
    machine_id: int
    line: int
    basket_id: int
    shift_id: Optional[int] = None
    total_weight: float = 0.0
    run_waste: float = 0.0
    setup_waste: float = 0.0

class WeavingProductionCreate(WeavingProductionBase):
    updated_by_id: Optional[int] = None

class WeavingProductionUpdate(BaseModel):
    machine_id: Optional[int] = None
    line: Optional[int] = None
    basket_id: Optional[int] = None
    shift_id: Optional[int] = None
    total_weight: Optional[float] = None
    run_waste: Optional[float] = None
    setup_waste: Optional[float] = None
    updated_by_id: Optional[int] = None

class WeavingProductionResponse(WeavingProductionBase):
    id: int
    updated_at: datetime
    updated_by_id: Optional[int] = None
    
    # Các trường mở rộng lấy từ Relationship trong SQLAlchemy
    machine: Optional[MachineShort] = None
    basket: Optional[BasketShort] = None
    shift: Optional[ShiftShort] = None
    updated_by: Optional[EmployeeShoft] = None

    class Config:
        from_attributes = True