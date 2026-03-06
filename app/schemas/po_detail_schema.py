from pydantic import BaseModel, ConfigDict, Field, computed_field
from typing import Optional
from datetime import date

class PurchaseOrderDetailBase(BaseModel):
    material_id: int
    currency: str = "USD" # Đổi mặc định thành USD
    
    quantity_kg: float = Field(..., gt=0, description="Số lượng mua tính bằng Kg")
    quantity_rolls: int = Field(default=0, ge=0, description="Số cuộn mua")
    
    unit_price: float = Field(..., gt=0, description="Đơn giá (theo USD)")
    is_pricing_by_roll: bool = False

    # --- CÁC TRƯỜNG LOGISTICS TỪ EXCEL ---
    ocean_freight: Optional[float] = None
    confirm_delivery: Optional[str] = None
    goods_readiness: Optional[str] = None
    shipping_line: Optional[str] = None
    forwarder: Optional[str] = None
    etd: Optional[date] = None
    eta: Optional[date] = None
    atd: Optional[date] = None
    booking_date: Optional[date] = None


class PurchaseOrderDetailCreate(PurchaseOrderDetailBase):
    pass


class PurchaseOrderDetailUpdate(BaseModel):
    # Cho phép cập nhật tất cả các trường (trừ id)
    material_id: Optional[int] = None
    currency: Optional[str] = None
    
    quantity_kg: Optional[float] = Field(None, gt=0)
    quantity_rolls: Optional[int] = Field(None, ge=0)
    
    unit_price: Optional[float] = Field(None, gt=0)
    is_pricing_by_roll: Optional[bool] = None
    
    # Cập nhật logistics
    ocean_freight: Optional[float] = None
    confirm_delivery: Optional[str] = None
    goods_readiness: Optional[str] = None
    shipping_line: Optional[str] = None
    forwarder: Optional[str] = None
    etd: Optional[date] = None
    eta: Optional[date] = None
    atd: Optional[date] = None
    booking_date: Optional[date] = None
    
    # Dành cho thủ kho khi nhận hàng
    received_quantity: Optional[float] = None
    received_rolls: Optional[int] = None


class PurchaseOrderDetailResponse(PurchaseOrderDetailBase):
    detail_id: int
    po_id: int
    line_total: float
    received_quantity: float
    received_rolls: int
    
    # [MỚI]: Tự động tính Số lượng (Kg) còn lại
    @computed_field
    @property
    def remaining_quantity(self) -> float:
        # max(0.0, ...) để tránh số âm trong trường hợp nhập kho lố số lượng PO
        return max(0.0, self.quantity_kg - self.received_quantity)
        
    # [MỚI]: Tự động tính Số cuộn còn lại
    @computed_field
    @property
    def remaining_rolls(self) -> int:
        return max(0, self.quantity_rolls - self.received_rolls)
    
    model_config = ConfigDict(from_attributes=True)