from pydantic import BaseModel, Field, computed_field
from typing import Optional
from datetime import datetime

# Base Schema (Các trường chung)
class MachineLogBase(BaseModel):
    status: str
    reason: Optional[str] = None
    image_url: Optional[str] = None

# Schema dùng để Tạo mới (Input)
class MachineLogCreate(MachineLogBase):
    machine_id: int

# Schema trả về cho Frontend (Output)
class MachineLogResponse(MachineLogBase):
    id: int
    machine_id: int
    start_time: datetime
    end_time: Optional[datetime] = None

    # [QUAN TRỌNG] Tự động tính thời gian (phút)
    @computed_field
    def duration_minutes(self) -> float:
        # Nếu đã kết thúc, lấy end_time. Nếu đang chạy, lấy thời gian hiện tại.
        end = self.end_time or datetime.now()
        
        # Tính khoảng cách thời gian
        delta = end - self.start_time
        
        # Trả về tổng số phút (làm tròn 1 số lẻ)
        return round(delta.total_seconds() / 60, 1)

    class Config:
        from_attributes = True # Để đọc được dữ liệu từ SQLAlchemy model