from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime
from app.models.batch import BatchQCStatus

class SupplierInBatch(BaseModel):
    supplier_id: int
    short_name: Optional[str] = None
    
    class Config:
        from_attributes = True

class BatchBase(BaseModel):
    supplier_batch_no: str
    material_id: int
    manufacture_date: Optional[date] = None
    expiry_date: Optional[date] = None
    origin_country: Optional[str] = None
    
    # [YÊU CẦU] Bổ sung location
    location: Optional[str] = None 
    
    qc_status: Optional[BatchQCStatus] = BatchQCStatus.PENDING
    qc_note: Optional[str] = None
    note: Optional[str] = None
    is_active: bool = True
    receipt_detail_id: Optional[int] = None

class BatchCreate(BatchBase):
    internal_batch_code: Optional[str] = None

class BatchUpdate(BaseModel):
    supplier_batch_no: Optional[str] = None
    manufacture_date: Optional[date] = None
    expiry_date: Optional[date] = None
    origin_country: Optional[str] = None
    
    # [YÊU CẦU] Cho phép update location
    location: Optional[str] = None 
    
    qc_status: Optional[BatchQCStatus] = None
    qc_note: Optional[str] = None
    note: Optional[str] = None
    is_active: Optional[bool] = None
    receipt_detail_id: Optional[int] = None # Cho phép sửa liên kết nếu cần

class BatchResponse(BatchBase):
    batch_id: int
    internal_batch_code: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    supplier: Optional[SupplierInBatch] = None
    
    # [MỚI] Trường này sẽ tự động lấy từ @property trong Model
    receipt_number: Optional[str] = None 

    class Config:
        from_attributes = True