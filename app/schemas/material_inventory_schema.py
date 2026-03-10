from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime

class MaterialInventoryBase(BaseModel):
    warehouse_id: int
    material_id: int
    batch_id: int
    location: Optional[str] = "N/A"
    
    # [CẬP NHẬT]
    number_of_pallets: Optional[int] = Field(0, ge=0)
    
    quantity_kg: float = Field(0.0, ge=0)
    quantity_cones: int = Field(0, ge=0)
    
    reserved_quantity_kg: Optional[float] = Field(0.0, ge=0)
    reserved_quantity_cones: Optional[int] = Field(0, ge=0)

class MaterialInventoryCreate(MaterialInventoryBase):
    pass

class MaterialInventoryUpdate(BaseModel):
    location: Optional[str] = None
    number_of_pallets: Optional[int] = Field(None, ge=0) # [CẬP NHẬT]
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
    
    # Thông tin mở rộng (Frontend dùng để hiển thị)
    warehouse_name: Optional[str] = None
    material_code: Optional[str] = None
    batch_code: Optional[str] = None
    po_number: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

class InventoryInitStock(BaseModel):
    """Schema dành riêng cho việc Khởi tạo tồn kho thủ công (Đầu kỳ)"""
    warehouse_id: int
    material_id: int
    supplier_batch_no: Optional[str] = None
    location: Optional[str] = "N/A"
    number_of_pallets: int = Field(0, ge=0)
    quantity_kg: float = Field(..., gt=0)
    quantity_cones: int = Field(..., ge=0)