from pydantic import BaseModel, Field
from typing import Optional

# ==========================================
# SCHEMAS CHO LOẠI NHÀ CUNG CẤP (CATEGORY)
# ==========================================

class SupplierCategoryBase(BaseModel):
    category_name: str = Field(..., description="Tên loại nhà cung cấp")
    description: Optional[str] = None

class SupplierCategoryCreate(SupplierCategoryBase):
    pass

class SupplierCategoryUpdate(BaseModel):
    category_name: Optional[str] = None
    description: Optional[str] = None

class SupplierCategoryResponse(SupplierCategoryBase):
    category_id: int

    class Config:
        from_attributes = True