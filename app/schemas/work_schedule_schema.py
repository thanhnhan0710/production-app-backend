from pydantic import BaseModel, Field
from datetime import date
from typing import Optional

# =======================
# NESTED SCHEMAS (Để hiển thị thông tin liên kết)
# =======================
# Giả sử bạn có model Employee và Shift, tạo schema rút gọn để hiển thị kèm
class EmployeeShort(BaseModel):
    employee_id: int
    full_name: str  # Giả sử bảng Employee có cột full_name
    class Config:
        from_attributes = True

class ShiftShort(BaseModel):
    shift_id: int
    shift_name: str # Giả sử bảng Shift có tên ca (Sáng, Chiều...)
    start_time: Optional[str] = None # Giờ bắt đầu
    end_time: Optional[str] = None   # Giờ kết thúc
    class Config:
        from_attributes = True

# =======================
# BASE SCHEMA
# =======================
class WorkScheduleBase(BaseModel):
    work_date: date = Field(..., description="Ngày làm việc (YYYY-MM-DD)")
    employee_id: int = Field(..., description="ID Nhân viên")
    shift_id: int = Field(..., description="ID Ca làm việc")

# =======================
# CREATE
# =======================
class WorkScheduleCreate(WorkScheduleBase):
    pass

# =======================
# UPDATE
# =======================
class WorkScheduleUpdate(BaseModel):
    work_date: Optional[date] = None
    employee_id: Optional[int] = None
    shift_id: Optional[int] = None

# =======================
# RESPONSE
# =======================
class WorkScheduleResponse(WorkScheduleBase):
    id: int
    
    # Nested objects (Optional vì có thể join hoặc không)
    employee: Optional[EmployeeShort] = None
    shift: Optional[ShiftShort] = None

    class Config:
        from_attributes = True