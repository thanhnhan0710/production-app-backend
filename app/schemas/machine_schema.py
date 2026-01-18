from pydantic import BaseModel
from typing import Optional
from app.models.machine import MachineStatus, MachineArea  # Import Enum từ model

class MachineBase(BaseModel):
    machine_name: str
    total_lines: Optional[int] = None
    purpose: Optional[str] = None
    
    # Sử dụng Enum để validate input chặt chẽ
    status: MachineStatus = MachineStatus.STOPPED 
    area: Optional[MachineArea] = None 

class MachineCreate(MachineBase):
    pass

class MachineUpdate(BaseModel):
    machine_name: Optional[str] = None
    total_lines: Optional[int] = None
    purpose: Optional[str] = None
    
    # Cho phép cập nhật từng phần (Optional)
    status: Optional[MachineStatus] = None
    area: Optional[MachineArea] = None

class MachineResponse(MachineBase):
    machine_id: int

    class Config:
        from_attributes = True

# [GIỮ LẠI TỪ HEAD] Class dùng riêng cho API cập nhật trạng thái (ví dụ: Báo hỏng, Bảo trì)
class MachineStatusUpdate(BaseModel):
    # Mình sửa từ 'str' thành 'MachineStatus' để validate chặt chẽ hơn
    status: MachineStatus 
    reason: Optional[str] = None
    image_url: Optional[str] = None