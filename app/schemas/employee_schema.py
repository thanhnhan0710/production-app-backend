from pydantic import BaseModel
from typing import Optional

class EmployeeBase(BaseModel):
    full_name: str
    email: Optional[str] = None 
    phone: Optional[str] = None
    address: Optional[str] = None
    position: str
    department_id: int
    group_id: Optional[int] = None # [MỚI] Thêm khóa ngoại Tổ nhân viên
    note: Optional[str] = None
    avatar_url: Optional[str] = None

class EmployeeCreate(EmployeeBase):
    pass

class EmployeeUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    position: Optional[str] = None
    department_id: Optional[int] = None
    group_id: Optional[int] = None # [MỚI] Thêm khóa ngoại Tổ nhân viên
    note: Optional[str] = None
    avatar_url: Optional[str] = None

class EmployeeResponse(EmployeeBase):
    employee_id: int

    class Config:
        from_attributes = True