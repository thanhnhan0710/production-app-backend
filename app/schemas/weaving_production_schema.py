# app/schemas/weaving_production_schema.py

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


# --- SCHEMAS BỔ TRỢ ---
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


class EmployeeShort(BaseModel):
    full_name: str

    class Config:
        from_attributes = True


# [MỚI] Schema rút gọn cho Phiếu rổ dệt (để hiển thị mã SP)
class WeavingTicketShort(BaseModel):
    id: int
    code: str
    product_item_code: Optional[str] = None  # Lấy từ product.item_code

    class Config:
        from_attributes = True


# --- MAIN SCHEMAS ---

class WeavingProductionBase(BaseModel):
    machine_id: int
    line: int
    basket_id: int
    weaving_ticket_id: Optional[int] = None   # [MỚI]
    shift_id: Optional[int] = None
    total_weight: float = 0.0
    run_waste: float = 0.0
    run_waste_reason: Optional[str] = None     # [MỚI]
    setup_waste: float = 0.0


class WeavingProductionCreate(WeavingProductionBase):
    updated_by_id: Optional[int] = None


class WeavingProductionUpdate(BaseModel):
    machine_id: Optional[int] = None
    line: Optional[int] = None
    basket_id: Optional[int] = None
    weaving_ticket_id: Optional[int] = None   # [MỚI]
    shift_id: Optional[int] = None
    total_weight: Optional[float] = None
    run_waste: Optional[float] = None
    run_waste_reason: Optional[str] = None     # [MỚI]
    setup_waste: Optional[float] = None
    updated_by_id: Optional[int] = None


class WeavingProductionResponse(WeavingProductionBase):
    id: int
    updated_at: datetime
    updated_by_id: Optional[int] = None

    machine: Optional[MachineShort] = None
    basket: Optional[BasketShort] = None
    shift: Optional[ShiftShort] = None
    updated_by: Optional[EmployeeShort] = None

    class Config:
        from_attributes = True