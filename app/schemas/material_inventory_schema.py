from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime

class MaterialInventoryBase(BaseModel):
    warehouse_id: int
    material_id: int
    batch_id: int
    location: Optional[str] = "N/A"
    
    quantity_kg: float = Field(0.0, ge=0)
    quantity_cones: int = Field(0, ge=0)
    
    reserved_quantity_kg: Optional[float] = Field(0.0, ge=0)
    reserved_quantity_cones: Optional[int] = Field(0, ge=0)

class MaterialInventoryCreate(MaterialInventoryBase):
    pass

class MaterialInventoryUpdate(BaseModel):
    location: Optional[str] = None
    quantity_kg: Optional[float] = Field(None, ge=0)
    quantity_cones: Optional[int] = Field(None, ge=0)
    reserved_quantity_kg: Optional[float] = Field(None, ge=0)
    reserved_quantity_cones: Optional[int] = Field(None, ge=0)
    last_counted_date: Optional[datetime] = None

class MaterialInventoryResponse(MaterialInventoryBase):
    inventory_id: int
    last_counted_date: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Ở Frontend, ta thường cần kèm tên kho, tên vật tư, mã lô để dễ hiển thị trên Table
    # (FastAPI sẽ tự động mapping nếu trong response DB query có join các bảng này)
    warehouse_name: Optional[str] = None
    material_code: Optional[str] = None
    batch_code: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)