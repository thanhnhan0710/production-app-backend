from pydantic import BaseModel
from typing import Optional
from app.schemas.product_type_schema import ProductTypeResponse

class ProductBase(BaseModel):
    item_code: str
    product_type_id: Optional[int] = None
    note: Optional[str] = None
    image_url: Optional[str] = None

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    item_code: Optional[str] = None
    product_type_id: Optional[int] = None
    note: Optional[str] = None
    image_url: Optional[str] = None

class ProductResponse(ProductBase):
    product_id: int
    # Gói thêm thông tin loại sản phẩm (tên, mô tả) để trả về cho Frontend hiển thị
    product_type: Optional[ProductTypeResponse] = None

    class Config:
        from_attributes = True