from pydantic import BaseModel, Field
from typing import Optional

# Import schema để hiển thị data lồng nhau
from app.schemas.material_type_schema import MaterialTypeResponse
from app.schemas.supplier_schema import SupplierResponse

class MaterialBase(BaseModel):
    material_code: str = Field(..., description="Mã nguyên vật liệu")
    material_name: str = Field(..., description="Tên nguyên vật liệu")
    type_id: Optional[int] = None
    supplier_id: Optional[int] = None
    
    color: Optional[str] = None
    dtex: Optional[int] = None
    filament: Optional[str] = None
    
    min_stock_level: Optional[float] = 0.0
    kg_per_bobbin: Optional[float] = None

class MaterialCreate(MaterialBase):
    pass

class MaterialUpdate(BaseModel):
    material_code: Optional[str] = None
    material_name: Optional[str] = None
    type_id: Optional[int] = None
    supplier_id: Optional[int] = None
    color: Optional[str] = None
    dtex: Optional[int] = None
    filament: Optional[str] = None
    min_stock_level: Optional[float] = None
    kg_per_bobbin: Optional[float] = None

class MaterialResponse(MaterialBase):
    material_id: int
    
    # Nested relations để UI hiển thị tên Loại & tên NCC thay vì chỉ hiện ID
    material_type: Optional[MaterialTypeResponse] = None
    supplier: Optional[SupplierResponse] = None

    class Config:
        from_attributes = True