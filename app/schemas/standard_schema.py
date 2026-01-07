from pydantic import BaseModel, Field
from typing import Optional

# =======================
# NESTED SCHEMAS
# =======================
class ProductShort(BaseModel):
    product_id: int
    item_code: str # [QUAN TRỌNG] Chỉ dùng item_code, bỏ 'name' vì model không có
    
    image_url: Optional[str] = None
    
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
    product_id: int
    dye_color_id: Optional[int] = None

    width_mm: str = Field(..., max_length=50)
    thickness_mm: str = Field(..., max_length=50)
    breaking_strength_dan: str = Field(..., max_length=50)
    elongation_at_load_percent: str = Field(..., max_length=50)

    color_fastness_dry: Optional[str] = Field(None, max_length=50)
    color_fastness_wet: Optional[str] = Field(None, max_length=50)
    delta_e: Optional[str] = Field(None, max_length=50)

    appearance: Optional[str] = None
    weft_density: str = Field(..., max_length=50)
    weight_gm: str = Field(..., max_length=50)

    note: Optional[str] = None

# =======================
# CREATE & UPDATE
# =======================
class StandardCreate(StandardBase):
    pass

class StandardUpdate(BaseModel):
    product_id: Optional[int] = None
    dye_color_id: Optional[int] = None
    width_mm: Optional[str] = None
    thickness_mm: Optional[str] = None
    breaking_strength_dan: Optional[str] = None
    elongation_at_load_percent: Optional[str] = None
    color_fastness_dry: Optional[str] = None
    color_fastness_wet: Optional[str] = None
    delta_e: Optional[str] = None
    appearance: Optional[str] = None
    weft_density: Optional[str] = None
    weight_gm: Optional[str] = None
    note: Optional[str] = None

# =======================
# RESPONSE
# =======================
class StandardResponse(StandardBase):
    standard_id: int
    
    product: Optional[ProductShort] = None
    dye_color: Optional[DyeColorShort] = None

    class Config:
        from_attributes = True