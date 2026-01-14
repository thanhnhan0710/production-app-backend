from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime

# =======================
# NESTED SCHEMAS (Để hiển thị thông tin kèm theo)
# =======================
class ProductShort(BaseModel):
    product_id: int
    item_code: Optional[str] = None # Khớp với model Product
    # name: Optional[str] = None
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

# =======================
# BASE SCHEMA
# =======================
class WeavingBasketTicketBase(BaseModel):
    code: str = Field(..., max_length=50, description="Mã phiếu (Unique)")
    
    # Sản xuất & Thiết bị
    product_id: int
    standard_id: int
    machine_id: int
    
    # [FIX] Model là Integer, nên Schema phải là int
    machine_line: Optional[int] = None 

    # Nguyên liệu
    yarn_load_date: date
    yarn_lot_id: Optional[int] = None
    basket_id: int

    gross_weight: Optional[float] = 0.0
    net_weight: Optional[float] = 0.0
    length_meters: Optional[float] = 0.0
    number_of_knots: Optional[int] = 0

# =======================
# CREATE (Lúc bắt đầu vào rổ)
# =======================
class WeavingTicketCreate(WeavingBasketTicketBase):
    employee_in_id: int
    time_in: Optional[datetime] = None 

    # [FIX] Thêm các trường này để tránh lỗi 422 nếu Frontend lỡ gửi lên
    # Mặc định là 0 khi tạo mới
    gross_weight: Optional[float] = 0.0
    net_weight: Optional[float] = 0.0
    length_meters: Optional[float] = 0.0
    number_of_knots: Optional[int] = 0
    
    # Cho phép nhận time_out/employee_out_id null từ frontend
    time_out: Optional[datetime] = None
    employee_out_id: Optional[int] = None

# =======================
# UPDATE (Lúc ra rổ / Chỉnh sửa)
# =======================
class WeavingTicketUpdate(BaseModel):
    # Cho phép sửa thông tin ban đầu nếu sai
    product_id: Optional[int] = None
    standard_id: Optional[int] = None
    machine_id: Optional[int] = None
    machine_line: Optional[int] = None
    basket_id: Optional[int] = None
    yarn_load_date: Optional[date] = None
    yarn_lot_id: Optional[int] = None
    
    # Thông tin kết thúc (Finish)
    time_out: Optional[datetime] = None
    employee_out_id: Optional[int] = None
    
    # Kết quả
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
    employee_in_id: int
    
    time_out: Optional[datetime] = None
    employee_out_id: Optional[int] = None

    gross_weight: Optional[float] = 0.0
    net_weight: Optional[float] = 0.0
    length_meters: Optional[float] = 0.0
    number_of_knots: Optional[int] = 0

    # Relationships
    product: Optional[ProductShort] = None
    basket: Optional[BasketShort] = None
    employee_in: Optional[EmployeeShort] = None
    employee_out: Optional[EmployeeShort] = None

    class Config:
        from_attributes = True