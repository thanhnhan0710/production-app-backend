from pydantic import BaseModel, ConfigDict, Field
from typing import Optional

class MaterialReceiptDetailBase(BaseModel):
    material_id: int
    
    # Số lượng tham khảo từ PO
    po_quantity_kg: Optional[float] = Field(0.0, ge=0)
    po_quantity_cones: Optional[int] = Field(0, ge=0)
    
    # Số lượng thực nhận vào kho
    received_quantity_kg: float = Field(..., gt=0, description="Khối lượng Kg thực nhập")
    received_quantity_cones: Optional[int] = Field(0, ge=0, description="Số cuộn thực nhập")
    
    number_of_pallets: Optional[int] = Field(0, ge=0)
    
    # Thông tin lô (để sinh ra Batch)
    supplier_batch_no: Optional[str] = None
    origin_country: Optional[str] = None
    location: Optional[str] = None
    note: Optional[str] = None

class MaterialReceiptDetailCreate(MaterialReceiptDetailBase):
    pass

class MaterialReceiptDetailUpdate(BaseModel):
    material_id: Optional[int] = None
    po_quantity_kg: Optional[float] = None
    po_quantity_cones: Optional[int] = None
    received_quantity_kg: Optional[float] = None
    received_quantity_cones: Optional[int] = None
    number_of_pallets: Optional[int] = None
    supplier_batch_no: Optional[str] = None
    origin_country: Optional[str] = None
    location: Optional[str] = None
    note: Optional[str] = None

class MaterialReceiptDetailResponse(MaterialReceiptDetailBase):
    detail_id: int
    receipt_id: int
    
    model_config = ConfigDict(from_attributes=True)