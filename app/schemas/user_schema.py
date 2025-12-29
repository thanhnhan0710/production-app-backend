from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict

# 1. Base Schema: Chứa các trường chung
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    is_active: Optional[bool] = True
    is_superuser: bool = False
    role: str = "staff"

# 2. Create Schema: Dùng khi tạo User mới (Bắt buộc có Password)
class UserCreate(UserBase):
    password: str = Field(..., min_length=6, description="Mật khẩu tối thiểu 6 ký tự")

# 3. Update Schema: Dùng khi cập nhật thông tin (Tất cả đều Optional)
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    role: Optional[str] = None

# 4. Response Schema: Dùng để trả về dữ liệu (Ẩn Password)
class UserResponse(UserBase):
    user_id: int
    
    # Cấu hình để Pydantic đọc được dữ liệu từ SQLAlchemy model
    model_config = ConfigDict(from_attributes=True)

# 5. Login Schema: Dùng riêng cho API đăng nhập
class UserLogin(BaseModel):
    email: EmailStr
    password: str

