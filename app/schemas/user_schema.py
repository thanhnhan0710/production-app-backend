<<<<<<< HEAD
# C:\Users\nhan_\Documents\production-app-backend\app\schemas\user_schema.py
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict

# [NEW] Schema nhỏ để hiển thị thông tin Employee lồng bên trong User
class EmployeeShortInfo(BaseModel):
    full_name: str
    # Có thể thêm các field khác nếu frontend cần
    model_config = ConfigDict(from_attributes=True)

# 1. Base Schema
=======
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, ConfigDict

# --- 0. Helper Schema (Định nghĩa trước để dùng trong UserResponse) ---
class EmployeeShort(BaseModel):
    employee_id: int
    full_name: Optional[str] = None
    
    # Cho phép đọc từ SQLAlchemy relationship
    model_config = ConfigDict(from_attributes=True)

# --- 1. Base Schema (Chứa các trường chung) ---
>>>>>>> c468be65d7388abd40a800c84aa27cfe56d2c0d3
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    is_active: Optional[bool] = True
    is_superuser: bool = False
    role: str = "staff"
<<<<<<< HEAD
    
    # [NEW] Thêm employee_id vào base
    employee_id: Optional[int] = None

# 2. Create Schema
=======
    employee_id: Optional[int] = None

# --- 2. Create Schema (Dùng khi tạo mới) ---
>>>>>>> c468be65d7388abd40a800c84aa27cfe56d2c0d3
class UserCreate(UserBase):
    email: EmailStr
    password: str
    full_name: str 

<<<<<<< HEAD
# 3. Update Schema
=======
# --- 3. Update Schema (Dùng khi cập nhật) ---
>>>>>>> c468be65d7388abd40a800c84aa27cfe56d2c0d3
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    role: Optional[str] = None
<<<<<<< HEAD
    
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
=======
    employee_id: Optional[int] = None

# --- 4. Response Schema (Dùng cho API trả về 1 User) ---
class UserResponse(UserBase):
    user_id: int
    
    # [MỚI - QUAN TRỌNG] Thêm trường này để trả về object Employee lồng bên trong
    # Frontend sẽ đọc: json['employee']['full_name']
    employee: Optional[EmployeeShort] = None 
    
    last_login: Optional[str] = None # Thêm trường này nếu bạn muốn hiển thị Last Login

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
>>>>>>> c468be65d7388abd40a800c84aa27cfe56d2c0d3
