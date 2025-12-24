from pydantic import BaseModel, Field
from typing import Optional

# =======================
# BASE SCHEMA
# =======================
class DyeColorBase(BaseModel):
    # Field(..., min_length=1) đảm bảo tên màu không được để rỗng
    color_name: str = Field(..., min_length=1, max_length=100, description="Tên màu nhuộm")
    
    # Hex code có thể null, nhưng nếu có thì max 20 ký tự
    hex_code: Optional[str] = Field(None, max_length=20, description="Mã màu Hex (Ví dụ: #FFFFFF)")
    
    note: Optional[str] = Field(None, max_length=150)

# =======================
# CREATE
# =======================
class DyeColorCreate(DyeColorBase):
    pass 
    # Kế thừa toàn bộ field từ Base

# =======================
# UPDATE
# =======================
class DyeColorUpdate(BaseModel):
    # Tất cả đều là Optional để cho phép sửa từng phần
    color_name: Optional[str] = Field(None, min_length=1, max_length=100)
    hex_code: Optional[str] = Field(None, max_length=20)
    note: Optional[str] = Field(None, max_length=150)

# =======================
# RESPONSE
# =======================
class DyeColorResponse(DyeColorBase):
    color_id: int

    class Config:
        from_attributes = True