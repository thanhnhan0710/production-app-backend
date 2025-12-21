from pydantic import BaseModel
from datetime import date
from typing import Optional, List

class ProductBase(BaseModel):
    item_code: str
    note: Optional[str] = None

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    item_code: Optional[str] = None
    note: Optional[str] = None

class ProductResponse(ProductBase):
    product_id: int

    class Config:
        from_attributes = True
