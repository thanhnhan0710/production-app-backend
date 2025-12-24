from pydantic import BaseModel, Field
from typing import Optional

# =======================
# NESTED SCHEMAS (Schemas phụ để hiển thị quan hệ)
# =======================
class ProductShort(BaseModel):
    product_id: int
    name: str # Giả sử bảng Product có cột name
    code: str # Giả sử bảng Product có cột code
    class Config:
        from_attributes = True

class DyeColorShort(BaseModel):
    color_id: int
    color_name: str
    hex_code: Optional[str] = None
    class Config:
        from_attributes = True

# =======================
# BASE SCHEMA
# =======================
class StandardBase(BaseModel):
    code: str = Field(..., max_length=50, description="Mã tiêu chuẩn (Unique)")
    
    # Khóa ngoại
    product_id: int
    dye_color_id: Optional[int] = None

    # Thông số vật lý (String vì model định nghĩa String)
    width_mm: str = Field(..., max_length=50)
    thickness_mm: str = Field(..., max_length=50)
    breaking_strength_dan: str = Field(..., max_length=50)
    elongation_at_load_percent: str = Field(..., max_length=50)

    # Thông số màu & Hóa học (Optional)
    color_fastness_dry: Optional[str] = Field(None, max_length=50)
    color_fastness_wet: Optional[str] = Field(None, max_length=50)
    delta_e: Optional[str] = Field(None, max_length=50)

    # Thông số dệt & Ngoại quan
    appearance: Optional[str] = None
    weft_density: str = Field(..., max_length=50)
    weight_gm: str = Field(..., max_length=50)

    note: Optional[str] = None

# =======================
# CREATE
# =======================
class StandardCreate(StandardBase):
    pass
    # Kế thừa toàn bộ vì hầu hết các trường đều bắt buộc (nullable=False)

# =======================
# UPDATE
# =======================
class StandardUpdate(BaseModel):
    code: Optional[str] = Field(None, max_length=50)
    product_id: Optional[int] = None
    dye_color_id: Optional[int] = None

    width_mm: Optional[str] = Field(None, max_length=50)
    thickness_mm: Optional[str] = Field(None, max_length=50)
    breaking_strength_dan: Optional[str] = Field(None, max_length=50)
    elongation_at_load_percent: Optional[str] = Field(None, max_length=50)

    color_fastness_dry: Optional[str] = Field(None, max_length=50)
    color_fastness_wet: Optional[str] = Field(None, max_length=50)
    delta_e: Optional[str] = Field(None, max_length=50)

    appearance: Optional[str] = None
    weft_density: Optional[str] = Field(None, max_length=50)
    weight_gm: Optional[str] = Field(None, max_length=50)

    note: Optional[str] = None

# =======================
# RESPONSE
# =======================
class StandardResponse(StandardBase):
    standard_id: int
    
    # Nested Relations (Optional vì có thể join hoặc không)
    product: Optional[ProductShort] = None
    dye_color: Optional[DyeColorShort] = None

    class Config:
        from_attributes = True