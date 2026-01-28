from pydantic import BaseModel, computed_field, Field
from typing import Optional

# Import các Schema cần thiết để hiển thị thông tin chi tiết (Nested)
from app.schemas.batch_schema import BatchResponse
from app.schemas.warehouse_schema import WarehouseResponse
from app.schemas.material_schema import MaterialResponse

# Schema hiển thị Tồn kho
class InventoryStockResponse(BaseModel):
    id: int
    material_id: int
    warehouse_id: int
    batch_id: int
    
    quantity_on_hand: float
    quantity_reserved: float
    
    # [MỚI] Các trường thông tin bổ sung từ quan hệ bảng
    received_quantity_cones: int = Field(default=0)
    number_of_pallets: int = Field(default=0)
    supplier_short_name: Optional[str] = None

    # Sử dụng @computed_field cho Pydantic v2 để tự động tính toán khi serialize
    @computed_field
    def available_quantity(self) -> float:
        return self.quantity_on_hand - self.quantity_reserved

    # --- THÔNG TIN CHI TIẾT (NESTED OBJECTS) ---
    batch: Optional[BatchResponse] = None
    warehouse: Optional[WarehouseResponse] = None
    material: Optional[MaterialResponse] = None 

    class Config:
        from_attributes = True

# Schema dùng cho Kiểm kê kho (Điều chỉnh số lượng bằng tay)
class InventoryAdjustment(BaseModel):
    material_id: int
    warehouse_id: int
    batch_id: int
    new_quantity: float
    reason: Optional[str] = None