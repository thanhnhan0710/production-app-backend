from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime

# =======================
# NESTED SCHEMAS
# =======================
class ProductShort(BaseModel):
    product_id: int
    item_code: Optional[str] = None
    class Config:
        from_attributes = True

class BasketShort(BaseModel):
    basket_id: int
    basket_code: str
    tare_weight: float
    class Config:
        from_attributes = True

class EmployeeShort(BaseModel):
    employee_id: int
    full_name: Optional[str] = None
    class Config:
        from_attributes = True

# [MỚI] Schema Supplier rút gọn
class SupplierShort(BaseModel):
    supplier_id: int
    supplier_short_name: Optional[str] = None
    class Config:
        from_attributes = True

# [MỚI] Schema Batch rút gọn (kèm Supplier)
class BatchInYarn(BaseModel):
    batch_id: int
    internal_batch_code: str
    supplier_batch_no: Optional[str] = None
    # Nested Supplier để lấy tên viết tắt
    supplier: Optional[SupplierShort] = None 
    class Config:
        from_attributes = True

# =======================
# WEAVING TICKET YARN SCHEMAS
# =======================
class WeavingTicketYarnBase(BaseModel):
    batch_id: int
    component_type: str 
    quantity: Optional[float] = 0.0 
    note: Optional[str] = None

class WeavingTicketYarnCreate(WeavingTicketYarnBase):
    pass

class WeavingTicketYarnResponse(WeavingTicketYarnBase):
    id: int
    
    # [MỚI] Include object Batch (chứa cả Supplier) vào response
    batch: Optional[BatchInYarn] = None 

    class Config:
        from_attributes = True

# =======================
# BASE SCHEMA (HEADER)
# =======================
class WeavingBasketTicketBase(BaseModel):
    code: str = Field(..., max_length=50, description="Mã phiếu (Unique)")
    
    product_id: Optional[int] = None
    standard_id: Optional[int] = None
    machine_id: Optional[int] = None
    machine_line: Optional[int] = None 

    yarn_load_date: Optional[date] = None
    basket_id: Optional[int] = None

    gross_weight: Optional[float] = 0.0
    net_weight: Optional[float] = 0.0
    length_meters: Optional[float] = 0.0
    number_of_knots: Optional[int] = 0

# =======================
# CREATE
# =======================
class WeavingTicketCreate(WeavingBasketTicketBase):
    employee_in_id: Optional[int] = None
    time_in: Optional[datetime] = None 
    yarns: Optional[List[WeavingTicketYarnCreate]] = [] # Input chỉ cần ID
    gross_weight: Optional[float] = 0.0
    net_weight: Optional[float] = 0.0
    length_meters: Optional[float] = 0.0
    number_of_knots: Optional[int] = 0
    time_out: Optional[datetime] = None
    employee_out_id: Optional[int] = None

# =======================
# UPDATE
# =======================
class WeavingTicketUpdate(BaseModel):
    product_id: Optional[int] = None
    standard_id: Optional[int] = None
    machine_id: Optional[int] = None
    machine_line: Optional[int] = None
    basket_id: Optional[int] = None
    yarn_load_date: Optional[date] = None
    time_out: Optional[datetime] = None
    employee_out_id: Optional[int] = None
    gross_weight: Optional[float] = Field(None, ge=0)
    net_weight: Optional[float] = Field(None)
    length_meters: Optional[float] = Field(None, ge=0)
    number_of_knots: Optional[int] = Field(None, ge=0)

# =======================
# RESPONSE
# =======================
class WeavingTicketResponse(WeavingBasketTicketBase):
    id: int
    time_in: Optional[datetime] = None
    employee_in_id: Optional[int] = None
    time_out: Optional[datetime] = None
    employee_out_id: Optional[int] = None

    gross_weight: Optional[float] = 0.0
    net_weight: Optional[float] = 0.0
    length_meters: Optional[float] = 0.0
    number_of_knots: Optional[int] = 0

    # Danh sách chi tiết sợi (Sẽ bao gồm batch và supplier info)
    yarns: List[WeavingTicketYarnResponse] = []

    # Relationships
    product: Optional[ProductShort] = None
    basket: Optional[BasketShort] = None
    employee_in: Optional[EmployeeShort] = None
    employee_out: Optional[EmployeeShort] = None

    class Config:
        from_attributes = True