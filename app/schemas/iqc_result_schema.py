from pydantic import BaseModel
from typing import Optional
from enum import Enum
from datetime import datetime

class IQCResultStatus(str, Enum):
    PASS = "Pass"
    FAIL = "Fail"
    PENDING = "Pending"

class IQCResultBase(BaseModel):
    batch_id: int
    tester_name: Optional[str] = None
    tensile_strength: Optional[float] = None
    elongation: Optional[float] = None
    color_fastness: Optional[float] = None
    final_result: IQCResultStatus = IQCResultStatus.PENDING
    note: Optional[str] = None

class IQCResultCreate(IQCResultBase):
    pass

class IQCResultUpdate(BaseModel):
    tester_name: Optional[str] = None
    tensile_strength: Optional[float] = None
    elongation: Optional[float] = None
    color_fastness: Optional[float] = None
    final_result: Optional[IQCResultStatus] = None
    note: Optional[str] = None

class IQCResultResponse(IQCResultBase):
    test_id: int
    test_date: datetime

    class Config:
        from_attributes = True