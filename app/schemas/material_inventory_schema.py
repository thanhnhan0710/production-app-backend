from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime

# =======================
# CÁC SCHEMA LỒNG NHAU (NESTED)
# Bổ sung để Pydantic tự động bóc tách dữ liệu từ hàm joinedload()
# =======================
class SimpleMaterial(BaseModel):
    material_code: str
    material_name: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class SimpleBatch(BaseModel):
    batch_code: str
    model_config = ConfigDict(from_attributes=True)

class SimpleWarehouse(BaseModel):
    warehouse_name: Optional[str] = None
    name: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

# =======================
# SCHEMA CHÍNH
# =======================
class MaterialInventoryBase(BaseModel):
    warehouse_id: int
    material_id: int
    batch_id: int
    location: Optional[str] = "N/A"
    
    number_of_pallets: Optional[int] = Field(0, ge=0)
    
    quantity_kg: float = Field(0.0, ge=0)
    quantity_cones: int = Field(0, ge=0)
    
    reserved_quantity_kg: Optional[float] = Field(0.0, ge=0)
    reserved_quantity_cones: Optional[int] = Field(0, ge=0)

class MaterialInventoryCreate(MaterialInventoryBase):
    pass

class MaterialInventoryUpdate(BaseModel):
    location: Optional[str] = None
    number_of_pallets: Optional[int] = Field(None, ge=0)
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
    
    # [GIỮ NGUYÊN] Các trường gán động cũ (để không phá vỡ logic cũ nếu có)
    warehouse_name: Optional[str] = None
    material_code: Optional[str] = None
    batch_code: Optional[str] = None
    po_number: Optional[str] = None
    
    # [MỚI]: Trả về các Object lồng nhau để Frontend dễ dàng lấy mã
    material: Optional[SimpleMaterial] = None
    batch: Optional[SimpleBatch] = None
    warehouse: Optional[SimpleWarehouse] = None
    
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