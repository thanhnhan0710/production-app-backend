from pydantic import BaseModel
from datetime import date
from typing import Optional, List


class YarnIssueSlipDetailBase(BaseModel):
    lot_code: str
    yarn_id: int

    machine_id: Optional[int] = None
    product_id: Optional[int] = None

    quantity: int
    unit_id: int

    shift_id: Optional[int] = None
    employee_id: int

class YarnIssueSlipDetailCreate(YarnIssueSlipDetailBase):
    issue_slip_id: int

class YarnIssueSlipDetailUpdate(BaseModel):
    machine_id: Optional[int] = None
    product_id: Optional[int] = None

    quantity: Optional[int] = None
    unit_id: Optional[int] = None

    shift_id: Optional[int] = None
    employee_id: Optional[int] = None

class YarnIssueSlipDetailResponse(YarnIssueSlipDetailBase):
    issue_detail_id: int
    issue_slip_id: int

    class Config:
        from_attributes = True

