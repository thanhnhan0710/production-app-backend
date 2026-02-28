from pydantic import BaseModel
from typing import Optional

# Đảm bảo KHÔNG có type_code ở đây
class ProductTypeBase(BaseModel):
    type_name: str
    description: Optional[str] = None

class ProductTypeCreate(ProductTypeBase):
    pass

class ProductTypeUpdate(BaseModel):
    type_name: Optional[str] = None
    description: Optional[str] = None

class ProductTypeResponse(ProductTypeBase):
    product_type_id: int

    class Config:
        from_attributes = True