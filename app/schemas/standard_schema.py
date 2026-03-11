from pydantic import BaseModel, Field, ConfigDict
from typing import Optional

# =======================
# NESTED SCHEMAS
# =======================
class ProductShort(BaseModel):
    product_id: int
    item_code: str
    
    image_url: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

# =======================
# BASE SCHEMA
# =======================
class StandardBase(BaseModel):
    product_id: int

    width_mm: str = Field(..., max_length=50)
    thickness_mm: str = Field(..., max_length=50)
    breaking_strength_dan: str = Field(..., max_length=50)
    elongation_at_load_percent: str = Field(..., max_length=50)
    
    curved: Optional[str] = Field(None, max_length=50) # [MỚI] Thêm trường curved

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
    width_mm: Optional[str] = None
    thickness_mm: Optional[str] = None
    breaking_strength_dan: Optional[str] = None
    elongation_at_load_percent: Optional[str] = None
    curved: Optional[str] = None # [MỚI]
    weft_density: Optional[str] = None
    weight_gm: Optional[str] = None
    note: Optional[str] = None

# =======================
# RESPONSE
# =======================
class StandardResponse(StandardBase):
    standard_id: int
    product: Optional[ProductShort] = None

    model_config = ConfigDict(from_attributes=True)