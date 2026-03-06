from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import date, datetime
from app.schemas.po_detail_schema import PurchaseOrderDetailCreate, PurchaseOrderDetailResponse

class PurchaseOrderHeaderBase(BaseModel):
    po_number: str
    vendor_id: int
    order_date: Optional[date] = None
    expected_arrival_date: Optional[date] = None
    incoterm_id: Optional[int] = None
    status_id: Optional[int] = None
    note: Optional[str] = None

class PurchaseOrderHeaderCreate(PurchaseOrderHeaderBase):
    details: List[PurchaseOrderDetailCreate]

class PurchaseOrderHeaderUpdate(BaseModel):
    po_number: Optional[str] = None
    vendor_id: Optional[int] = None
    order_date: Optional[date] = None
    expected_arrival_date: Optional[date] = None
    incoterm_id: Optional[int] = None
    status_id: Optional[int] = None
    note: Optional[str] = None
    # [MỚI]: Phải thêm trường details vào Update thì Backend mới nhận được mảng gửi lên để sửa
    details: Optional[List[PurchaseOrderDetailCreate]] = None

class PurchaseOrderHeaderResponse(PurchaseOrderHeaderBase):
    po_id: int
    total_amount: float
    created_at: datetime
    updated_at: Optional[datetime] = None
    details: List[PurchaseOrderDetailResponse] = []
    
    model_config = ConfigDict(from_attributes=True)