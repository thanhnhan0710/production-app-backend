from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime

# =======================
# NESTED SCHEMAS (Để hiển thị thông tin kèm theo)
# =======================
class ProductShort(BaseModel):
    product_id: int
    # name: str # Thêm nếu model Product có cột name
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
    # full_name: str
    class Config:
        from_attributes = True

# =======================
# BASE SCHEMA
# =======================
class WeavingBasketTicketBase(BaseModel):
    code: str = Field(..., max_length=50, description="Mã phiếu (Unique)")
    
    # Sản xuất & Thiết bị
    product_id: int
    standard_id: int
    machine_id: int
    machine_line: Optional[str] = Field(None, max_length=50)

    # Nguyên liệu
    yarn_load_date: date
    yarn_lot_id: Optional[int] = None
    basket_id: int

# =======================
# CREATE (Lúc bắt đầu vào rổ)
# =======================
class WeavingTicketCreate(WeavingBasketTicketBase):
    employee_in_id: int
    time_in: Optional[datetime] = None # Nếu không nhập, lấy giờ hệ thống

# =======================
# UPDATE (Lúc ra rổ / Chỉnh sửa)
# =======================
class WeavingTicketUpdate(BaseModel):
    # Cho phép sửa thông tin ban đầu nếu sai
    product_id: Optional[int] = None
    standard_id: Optional[int] = None
    machine_id: Optional[int] = None
    basket_id: Optional[int] = None
    
    # Thông tin kết thúc (Finish)
    time_out: Optional[datetime] = None
    employee_out_id: Optional[int] = None
    
    # Kết quả
    gross_weight: Optional[float] = Field(None, gt=0, description="Tổng trọng lượng (kg)")
    net_weight: Optional[float] = Field(None, description="Tự động tính nếu nhập Gross Weight")
    length_meters: Optional[float] = Field(None, gt=0)
    number_of_knots: Optional[int] = Field(None, ge=0)

# =======================
# RESPONSE
# =======================
class WeavingTicketResponse(WeavingBasketTicketBase):
    id: int
    time_in: Optional[datetime]
    employee_in_id: int
    
    time_out: Optional[datetime]
    employee_out_id: Optional[int]

    gross_weight: Optional[float]
    net_weight: Optional[float]
    length_meters: Optional[float]
    number_of_knots: Optional[int]

    # Relationships
    product: Optional[ProductShort] = None
    basket: Optional[BasketShort] = None
    employee_in: Optional[EmployeeShort] = None
    employee_out: Optional[EmployeeShort] = None

    class Config:
        from_attributes = True