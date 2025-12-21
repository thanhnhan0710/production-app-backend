from pydantic import BaseModel
from datetime import date
from typing import Optional, List

class MaterialIssueSlipDetailBase(BaseModel):
    issue_slip_id: int
    material_id: int
    quantity: float
    unit_id: int
    shift_id: int
    employee_id: int

class MaterialIssueSlipDetailCreate(MaterialIssueSlipDetailBase):
    pass

class MaterialIssueSlipDetailUpdate(BaseModel):
    material_id: Optional[int] = None
    quantity: Optional[float] = None
    unit_id: Optional[int] = None
    shift_id: Optional[int] = None
    employee_id: Optional[int] = None

class MaterialIssueSlipDetailResponse(MaterialIssueSlipDetailBase):
    issue_detail_id: int

    class Config:
        from_attributes = True
