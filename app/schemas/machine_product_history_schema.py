from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class MachineProductAssign(BaseModel):
    product_id: int
    line_number: int = 1 # [MỚI]
    notes: Optional[str] = None

class MachineProductHistoryUpdate(BaseModel):
    product_id: Optional[int] = None
    line_number: Optional[int] = None # [MỚI]
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    notes: Optional[str] = None

class ProductBasicInfo(BaseModel):
    product_id: int
    item_code: Optional[str] = None
    class Config:
        from_attributes = True

class MachineBasicInfo(BaseModel):
    machine_id: int
    machine_name: str
    class Config:
        from_attributes = True

class MachineProductHistoryResponse(BaseModel):
    id: int
    machine_id: int
    product_id: int
    line_number: int # [MỚI]
    start_time: datetime
    end_time: Optional[datetime] = None
    notes: Optional[str] = None
    
    product: Optional[ProductBasicInfo] = None
    machine: Optional[MachineBasicInfo] = None

    class Config:
        from_attributes = True