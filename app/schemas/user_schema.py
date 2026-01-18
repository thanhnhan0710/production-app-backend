# C:\Users\nhan_\Documents\production-app-backend\app\schemas\user_schema.py
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict

# [NEW] Schema nhỏ để hiển thị thông tin Employee lồng bên trong User
class EmployeeShortInfo(BaseModel):
    full_name: str
    # Có thể thêm các field khác nếu frontend cần
    model_config = ConfigDict(from_attributes=True)

# 1. Base Schema
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    is_active: Optional[bool] = True
    is_superuser: bool = False
    role: str = "staff"
    
    # [NEW] Thêm employee_id vào base
    employee_id: Optional[int] = None

# 2. Create Schema
class UserCreate(UserBase):
    email: EmailStr
    password: str
    full_name: str 

# 3. Update Schema
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    role: Optional[str] = None
    
    # [NEW] Cho phép update employee_id
    employee_id: Optional[int] = None

# 4. Response Schema
class UserResponse(UserBase):
    user_id: int
    
    # [NEW] Trả về object employee để frontend lấy được full_name
    # Frontend gọi: json['employee']['full_name']
    employee: Optional[EmployeeShortInfo] = None
    
    model_config = ConfigDict(from_attributes=True)

# 5. Login Schema
class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserListResponse(BaseModel):
    data: List[UserResponse]  # Quan trọng: Khai báo list này chứa UserResponse
    total: int
    skip: int
    limit: int