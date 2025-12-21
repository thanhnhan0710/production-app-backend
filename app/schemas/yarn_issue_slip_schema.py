from pydantic import BaseModel
from datetime import date
from typing import Optional, List

from app.schemas.yarn_issue_slip_detail_schema import YarnIssueSlipDetailResponse

class YarnIssueSlipBase(BaseModel):
    issue_date: date
    note: Optional[str] = None

class YarnIssueSlipCreate(YarnIssueSlipBase):
    pass

class YarnIssueSlipUpdate(BaseModel):
    issue_date: Optional[date] = None
    note: Optional[str] = None

class YarnIssueSlipResponse(YarnIssueSlipBase):
    issue_slip_id: int

    class Config:
        from_attributes = True

class YarnIssueSlipDetailShort(YarnIssueSlipDetailResponse):
    pass

class YarnIssueSlipDetailView(YarnIssueSlipResponse):
    details: List[YarnIssueSlipDetailShort] = []
