from pydantic import BaseModel
from typing import Optional

class EmployeeBase(BaseModel):
    full_name: str
    # [ĐÃ SỬA]: Chuyển EmailStr thành Optional[str]
    email: Optional[str] = None 
    phone: Optional[str] = None
    address: Optional[str] = None
    position: str
    department_id: int
    note: Optional[str] = None
    avatar_url: Optional[str] = None

class EmployeeCreate(EmployeeBase):
    pass

class EmployeeUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None # [ĐÃ SỬA]
    phone: Optional[str] = None
    address: Optional[str] = None
    position: Optional[str] = None
    department_id: Optional[int] = None
    note: Optional[str] = None
    avatar_url: Optional[str] = None

class EmployeeResponse(EmployeeBase):
    employee_id: int

    class Config:
        from_attributes = True