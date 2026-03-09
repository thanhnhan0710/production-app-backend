from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import date, datetime

class MaterialBatchBase(BaseModel):
    batch_code: str
    material_id: int
    receipt_detail_id: Optional[int] = None
    
    supplier_batch_no: Optional[str] = None
    origin_country: Optional[str] = None
    manufacturing_date: Optional[date] = None
    expiration_date: Optional[date] = None
    
    initial_quantity_kg: float = Field(0.0, ge=0)
    initial_quantity_cones: int = Field(0, ge=0)
    
    status: Optional[str] = "Available"

class MaterialBatchCreate(MaterialBatchBase):
    pass

class MaterialBatchUpdate(BaseModel):
    batch_code: Optional[str] = None
    supplier_batch_no: Optional[str] = None
    origin_country: Optional[str] = None
    manufacturing_date: Optional[date] = None
    expiration_date: Optional[date] = None
    status: Optional[str] = None

class MaterialBatchResponse(MaterialBatchBase):
    batch_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)