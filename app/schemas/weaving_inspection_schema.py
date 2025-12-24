from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

# =======================
# NESTED SCHEMAS (Hiển thị tên thay vì chỉ ID)
# =======================
class EmployeeShort(BaseModel):
    employee_id: int
    full_name: str # Giả sử model Employee có full_name
    class Config:
        from_attributes = True

class ShiftShort(BaseModel):
    shift_id: int
    shift_name: str # Giả sử model Shift có shift_name
    class Config:
        from_attributes = True

# =======================
# BASE SCHEMA
# =======================
class WeavingInspectionBase(BaseModel):
    weaving_basket_ticket_id: int = Field(..., description="ID của phiếu rổ dệt cần kiểm tra")
    stage_name: str = Field(..., min_length=1, max_length=50, description="Giai đoạn: Lần 1, Lần 2, Ra rổ...")
    
    # Thông tin người kiểm tra
    employee_id: int
    shift_id: int

    # Các thông số (Optional vì có thể không đo hết tất cả trong 1 lần)
    width_mm: Optional[float] = Field(None, gt=0, description="Chiều rộng (mm)")
    weft_density: Optional[float] = Field(None, gt=0, description="Mật độ sợi ngang")
    tension_dan: Optional[float] = Field(None, gt=0, description="Lực căng (daN)")
    thickness_mm: Optional[float] = Field(None, gt=0, description="Độ dày (mm)")
    weight_gm: Optional[float] = Field(None, gt=0, description="Trọng lượng (g/m)")
    bowing: Optional[float] = Field(None, description="Độ cong (mm hoặc %)")

# =======================
# CREATE
# =======================
class WeavingInspectionCreate(WeavingInspectionBase):
    # Thời gian kiểm tra: Nếu không gửi lên, server sẽ lấy giờ hiện tại
    inspection_time: Optional[datetime] = None

# =======================
# UPDATE
# =======================
class WeavingInspectionUpdate(BaseModel):
    # Cho phép sửa mọi trường
    weaving_basket_ticket_id: Optional[int] = None
    stage_name: Optional[str] = Field(None, min_length=1, max_length=50)
    employee_id: Optional[int] = None
    shift_id: Optional[int] = None
    inspection_time: Optional[datetime] = None

    width_mm: Optional[float] = Field(None, gt=0)
    weft_density: Optional[float] = Field(None, gt=0)
    tension_dan: Optional[float] = Field(None, gt=0)
    thickness_mm: Optional[float] = Field(None, gt=0)
    weight_gm: Optional[float] = Field(None, gt=0)
    bowing: Optional[float] = None

# =======================
# RESPONSE
# =======================
class WeavingInspectionResponse(WeavingInspectionBase):
    id: int
    inspection_time: datetime

    # Nested objects
    employee: Optional[EmployeeShort] = None
    shift: Optional[ShiftShort] = None

    class Config:
        from_attributes = True