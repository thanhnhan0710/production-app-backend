from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# Form Request: Gán sản phẩm cho máy
class MachineProductAssign(BaseModel):
    product_id: int
    notes: Optional[str] = None

# [MỚI] Form Request: Cập nhật lịch sử (Sửa lỗi sai)
class MachineProductHistoryUpdate(BaseModel):
    product_id: Optional[int] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    notes: Optional[str] = None

class ProductBasicInfo(BaseModel):
    product_id: int
    item_code: Optional[str] = None

    class Config:
        from_attributes = True

# [MỚI] Thêm thông tin máy
class MachineBasicInfo(BaseModel):
    machine_id: int
    machine_name: str
    class Config:
        from_attributes = True

# Response: Trả về lịch sử
class MachineProductHistoryResponse(BaseModel):
    id: int
    machine_id: int
    product_id: int
    start_time: datetime
    end_time: Optional[datetime] = None
    notes: Optional[str] = None
    
    product: Optional[ProductBasicInfo] = None

    class Config:
        from_attributes = True