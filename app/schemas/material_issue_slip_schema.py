from pydantic import BaseModel
from datetime import date
from typing import Optional, List

class MaterialIssueSlipBase(BaseModel):
    issue_date: date
    note: Optional[str] = None

class MaterialIssueSlipCreate(MaterialIssueSlipBase):
    pass

class MaterialIssueSlipUpdate(BaseModel):
    issue_date: Optional[date] = None
    note: Optional[str] = None

class MaterialIssueSlipResponse(MaterialIssueSlipBase):
    issue_slip_id: int

    class Config:
        from_attributes = True
