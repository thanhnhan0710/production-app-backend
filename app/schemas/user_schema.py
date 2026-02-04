from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator

# --- 0. Helper Schema (Định nghĩa trước để dùng trong UserResponse) ---
class EmployeeShort(BaseModel):
    employee_id: int
    full_name: Optional[str] = None
    
    # Cho phép đọc từ SQLAlchemy relationship
    model_config = ConfigDict(from_attributes=True)

# --- 1. Base Schema (Chứa các trường chung) ---
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    is_active: Optional[bool] = True
    is_superuser: bool = False
    role: str = "staff"
    @field_validator('role')
    def normalize_role(cls, v):
        return v.lower() if v else 'staff'
    
    # Thêm employee_id vào base để frontend có thể gửi lên hoặc nhận về ở mọi nơi
    employee_id: Optional[int] = None

# --- 2. Create Schema (Dùng khi tạo mới) ---
class UserCreate(UserBase):
    email: EmailStr
    password: str
    full_name: str 

# --- 3. Update Schema (Dùng khi cập nhật) ---
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    role: Optional[str] = None
    @field_validator('role')
    def normalize_role(cls, v):
        return v.lower() if v else 'staff'
    
    # Cho phép update employee_id
    employee_id: Optional[int] = None

# --- 4. Response Schema (Dùng cho API trả về 1 User) ---
class UserResponse(UserBase):
    user_id: int
    
    # [QUAN TRỌNG] Thêm trường này để trả về object Employee lồng bên trong
    # Frontend sẽ đọc: json['employee']['full_name']
    employee: Optional[EmployeeShort] = None 
    
    last_login: Optional[str] = None # Thêm trường này để hiển thị thời gian đăng nhập cuối

    model_config = ConfigDict(from_attributes=True)

# --- 5. List Response Schema (Dùng cho API trả về danh sách) ---
class UserListResponse(BaseModel):
    data: List[UserResponse] 
    total: int
    skip: int
    limit: int

# --- 6. Login Schema ---
class UserLogin(BaseModel):
    email: EmailStr
    password: str