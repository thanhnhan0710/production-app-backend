from pydantic import BaseModel
from typing import Optional

class EmployeeGroupBase(BaseModel):
    group_name: str
    description: Optional[str] = None
    department_id: Optional[int] = None

class EmployeeGroupCreate(EmployeeGroupBase):
    pass

class EmployeeGroupUpdate(BaseModel):
    group_name: Optional[str] = None
    description: Optional[str] = None
    department_id: Optional[int] = None

class EmployeeGroupResponse(EmployeeGroupBase):
    group_id: int

    class Config:
        from_attributes = True