from pydantic import BaseModel
from typing import Optional

# Base chung
class DepartmentBase(BaseModel):
    department_name: str
    description: Optional[str] = None

# Schema khi tạo mới (Create)
class DepartmentCreate(DepartmentBase):
    pass

# Schema khi cập nhật (Update)
class DepartmentUpdate(BaseModel):
    department_name: Optional[str] = None
    description: Optional[str] = None

# Schema khi trả về Client (Response)
class DepartmentResponse(DepartmentBase):
    department_id: int

    class Config:
        from_attributes = True # Để đọc được dữ liệu từ ORM