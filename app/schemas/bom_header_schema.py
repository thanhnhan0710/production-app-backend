from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from app.schemas.bom_detail_schema import BOMDetailResponse # Để dùng cho nested response

class BOMHeaderBase(BaseModel):
    product_id: int
    bom_code: str
    bom_name: Optional[str] = None
    version: int = 1
    is_active: bool = True
    base_quantity: float = 1.0

class BOMHeaderCreate(BOMHeaderBase):
    pass

class BOMHeaderUpdate(BaseModel):
    product_id: Optional[int] = None
    bom_code: Optional[str] = None
    bom_name: Optional[str] = None
    version: Optional[int] = None
    is_active: Optional[bool] = None
    base_quantity: Optional[float] = None

class BOMHeaderResponse(BOMHeaderBase):
    bom_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# --- Bổ sung: Schema trả về Header kèm danh sách Detail ---
# Dùng cho API GET /boms/{id}
class BOMHeaderWithDetailsResponse(BOMHeaderResponse):
    bom_details: List[BOMDetailResponse] = []