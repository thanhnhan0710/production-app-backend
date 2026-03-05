from pydantic import BaseModel, Field
from typing import Optional
from app.schemas.supplier_category_schema import SupplierCategoryResponse

# ==========================================
# SCHEMAS CHO NHÀ CUNG CẤP (SUPPLIER)
# ==========================================

class SupplierBase(BaseModel):
    supplier_name: str = Field(..., description="Tên đầy đủ của nhà cung cấp")
    short_name: Optional[str] = None
    address: Optional[str] = None
    is_active: Optional[bool] = True
    category_id: Optional[int] = Field(None, description="ID của Loại nhà cung cấp")

class SupplierCreate(SupplierBase):
    pass

class SupplierUpdate(BaseModel):
    supplier_name: Optional[str] = None
    short_name: Optional[str] = None
    address: Optional[str] = None
    is_active: Optional[bool] = None
    category_id: Optional[int] = None

class SupplierResponse(SupplierBase):
    supplier_id: int
    
    # Kèm theo thông tin Loại NCC để Frontend dễ hiển thị
    category: Optional[SupplierCategoryResponse] = None

    class Config:
        from_attributes = True