from pydantic import BaseModel, ConfigDict, Field
from typing import Optional

class PurchaseOrderDetailBase(BaseModel):
    material_id: int
    currency: str = "VND"
    exchange_rate: float = 1.0
    
    quantity_kg: float = Field(..., gt=0, description="Số lượng mua tính bằng Kg")
    quantity_rolls: int = Field(default=0, ge=0, description="Số cuộn mua")
    
    unit_price: float = Field(..., gt=0, description="Đơn giá (theo ngoại tệ)")
    is_pricing_by_roll: bool = False

class PurchaseOrderDetailCreate(PurchaseOrderDetailBase):
    pass

class PurchaseOrderDetailUpdate(BaseModel):
    # Cho phép cập nhật tất cả các trường (trừ id)
    material_id: Optional[int] = None
    currency: Optional[str] = None
    exchange_rate: Optional[float] = None
    
    quantity_kg: Optional[float] = Field(None, gt=0)
    quantity_rolls: Optional[int] = Field(None, ge=0)
    
    unit_price: Optional[float] = Field(None, gt=0)
    is_pricing_by_roll: Optional[bool] = None
    
    # Dành cho thủ kho khi nhận hàng
    received_quantity: Optional[float] = None
    received_rolls: Optional[int] = None

class PurchaseOrderDetailResponse(PurchaseOrderDetailBase):
    detail_id: int
    po_id: int
    line_total: float
    received_quantity: float
    received_rolls: int
    
    model_config = ConfigDict(from_attributes=True)