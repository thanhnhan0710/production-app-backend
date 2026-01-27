from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime

# Import các schema lồng nhau
from app.schemas.import_declaration_schema import ImportDeclarationResponse
from app.schemas.material_schema import MaterialResponse
from app.schemas.purchase_order_schema import POHeaderResponse
from app.schemas.warehouse_schema import WarehouseResponse

# --- DETAIL SCHEMAS ---
class MaterialReceiptDetailBase(BaseModel):
    material_id: int
    
    # 1. Số lượng theo chứng từ
    po_quantity_kg: float = Field(default=0.0, description="Số lượng Kg trên chứng từ")
    po_quantity_cones: int = Field(default=0, description="Số lượng Cuộn trên chứng từ")
    
    # 2. Số lượng thực nhận
    received_quantity_kg: float = Field(..., description="Số lượng Kg thực nhận")
    received_quantity_cones: int = Field(default=0, description="Số lượng Cuộn thực nhận")
    
    # 3. Thông tin đóng gói & Batch
    number_of_pallets: int = Field(default=0, description="Tổng số Pallet/Kiện")
    supplier_batch_no: Optional[str] = None 
    
    # Trường xuất xứ
    origin_country: Optional[str] = None
    
    # [MỚI] Thêm location vào Base để Create/Response đều nhận được
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
    
    # [MỚI] Cho phép update location
    location: Optional[str] = None 
    
    note: Optional[str] = None

class MaterialReceiptDetailResponse(MaterialReceiptDetailBase):
    detail_id: int
    receipt_id: int
    material: Optional[MaterialResponse] = None 

    class Config:
        from_attributes = True

# --- HEADER SCHEMAS ---
class MaterialReceiptBase(BaseModel):
    receipt_number: str
    receipt_date: Optional[date] = None
    po_header_id: Optional[int] = None
    declaration_id: Optional[int] = None
    warehouse_id: int
    container_no: Optional[str] = None
    seal_no: Optional[str] = None
    note: Optional[str] = None
    created_by: Optional[str] = None

class MaterialReceiptCreate(MaterialReceiptBase):
    details: List[MaterialReceiptDetailCreate] = []

class MaterialReceiptUpdate(BaseModel):
    receipt_number: Optional[str] = None
    receipt_date: Optional[date] = None
    po_header_id: Optional[int] = None
    declaration_id: Optional[int] = None
    warehouse_id: Optional[int] = None
    container_no: Optional[str] = None
    seal_no: Optional[str] = None
    note: Optional[str] = None
    created_by: Optional[str] = None

class MaterialReceiptResponse(MaterialReceiptBase):
    receipt_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    details: List[MaterialReceiptDetailResponse] = []
    
    warehouse: Optional[WarehouseResponse] = None
    # Nếu có schema PO/Declaration response thì uncomment
    po_header: Optional[POHeaderResponse] = None 
    declaration: Optional[ImportDeclarationResponse] = None

    class Config:
        from_attributes = True

# --- FILTER SCHEMA ---
class MaterialReceiptFilter(BaseModel):
    search: Optional[str] = None
    po_id: Optional[int] = None
    declaration_id: Optional[int] = None
    from_date: Optional[date] = None
    to_date: Optional[date] = None