from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import date, datetime
from app.schemas.material_receipt_detail_schema import MaterialReceiptDetailCreate, MaterialReceiptDetailResponse

class MaterialReceiptBase(BaseModel):
    receipt_number: Optional[str] = None # Có thể null nếu hệ thống tự sinh mã
    receipt_date: Optional[date] = None
    po_header_id: Optional[int] = None
    warehouse_id: int
    
    container_no: Optional[str] = None
    seal_no: Optional[str] = None
    status: Optional[str] = "Draft"
    note: Optional[str] = None
    created_by: Optional[str] = None

class MaterialReceiptCreate(MaterialReceiptBase):
    # Khi tạo phiếu nhập, bắt buộc phải truyền kèm danh sách các dòng vật tư
    details: List[MaterialReceiptDetailCreate]

class MaterialReceiptUpdate(BaseModel):
    receipt_number: Optional[str] = None
    receipt_date: Optional[date] = None
    po_header_id: Optional[int] = None
    warehouse_id: Optional[int] = None
    container_no: Optional[str] = None
    seal_no: Optional[str] = None
    status: Optional[str] = None
    note: Optional[str] = None
    
    details: Optional[List[MaterialReceiptDetailCreate]] = None

class MaterialReceiptResponse(MaterialReceiptBase):
    receipt_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Trả về cả danh sách chi tiết
    details: List[MaterialReceiptDetailResponse] = []
    
    model_config = ConfigDict(from_attributes=True)