from pydantic import BaseModel, Field
from typing import Optional
from app.schemas.unit_schema import UnitResponse

# 1. Base Schema: Chứa các trường chung bắt buộc
class MaterialBase(BaseModel):
    material_code: str = Field(..., title="Mã sợi", max_length=50, example="POY-1000D-BLACK")
    material_name: Optional[str] = Field(None, title="Tên sợi", max_length=200, example="03300-PES-WEISS")
    material_type: Optional[str] = Field(None, title="Loại sợi", max_length=100)
    
    # Thông số kỹ thuật
    spec_denier: Optional[str] = Field(None, title="Denier", max_length=50)
    spec_filament: Optional[int] = Field(None, title="Số lượng sơ")
    hs_code: Optional[str] = Field(None, title="HS Code", max_length=20)
    
    # Quản lý kho
    min_stock_level: float = Field(0.0, title="Mức tồn kho tối thiểu")

    # ID của Unit (Khi tạo/sửa chỉ cần truyền ID)
    uom_base_id: int = Field(..., title="ID Đơn vị mua")
    uom_production_id: int = Field(..., title="ID Đơn vị sản xuất")

# 2. Schema dùng để TẠO MỚI (Create)
class MaterialCreate(MaterialBase):
    pass 
    # Có thể pass vì các trường required đã có trong MaterialBase.
    # Nếu có logic validation riêng cho lúc tạo, viết ở đây.

# 3. Schema dùng để CẬP NHẬT (Update)
# Tất cả các trường đều là Optional để hỗ trợ PATCH (sửa 1 phần)
class MaterialUpdate(BaseModel):
    material_code: Optional[str] = None
    material_name: Optional[str] = None
    material_type: Optional[str] = None
    spec_denier: Optional[str] = None
    spec_filament: Optional[int] = None
    hs_code: Optional[str] = None
    min_stock_level: Optional[float] = None
    uom_base_id: Optional[int] = None
    uom_production_id: Optional[int] = None

# 4. Schema dùng để TRẢ VỀ (Response)
class MaterialResponse(MaterialBase):
    id: int
    uom_base: Optional[UnitResponse] = None
    uom_production: Optional[UnitResponse] = None
    class Config:
        from_attributes = True # Quan trọng: Cho phép đọc dữ liệu từ SQLAlchemy model



class MaterialDetailResponse(MaterialResponse):
     uom_base: Optional[UnitResponse] = None
     uom_production: Optional[UnitResponse] = None