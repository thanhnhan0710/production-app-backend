from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.schemas.batch_schema import BatchResponse # Để hiển thị thông tin Batch
from app.schemas.unit_schema import UnitResponse   # Để hiển thị đơn vị tính

# Schema hiển thị
class InventoryStockResponse(BaseModel):
    id: int
    material_id: int
    warehouse_id: int
    batch_id: int
    
    quantity_on_hand: float
    quantity_reserved: float
    available_quantity: float # Computed field: on_hand - reserved
    
    batch: Optional[BatchResponse] = None
    
    class Config:
        from_attributes = True

# Schema dùng cho Kiểm kê kho (Điều chỉnh số lượng bằng tay)
class InventoryAdjustment(BaseModel):
    material_id: int
    warehouse_id: int
    batch_id: int
    new_quantity: float # Số lượng thực tế kiểm đếm được
    reason: Optional[str] = None