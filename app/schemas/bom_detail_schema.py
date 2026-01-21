from pydantic import BaseModel, Field
from typing import Optional
from app.models.bom_detail import BOMComponentType # Import Enum từ model

class BOMDetailBase(BaseModel):
    # Dùng material_id thay vì object Material
    material_id: int 
    component_type: BOMComponentType
    
    number_of_ends: Optional[int] = 0
    quantity_standard: float
    wastage_rate: Optional[float] = 0.0
    quantity_gross: float # Có thể tính toán ở FE hoặc BE, nhưng cần gửi lên
    
    note: Optional[str] = None

class BOMDetailCreate(BOMDetailBase):
    # Khi tạo detail, thường cần biết nó thuộc BOM nào
    bom_id: int 

class BOMDetailUpdate(BaseModel):
    # Cho phép update từng trường riêng lẻ
    material_id: Optional[int] = None
    component_type: Optional[BOMComponentType] = None
    number_of_ends: Optional[int] = None
    quantity_standard: Optional[float] = None
    wastage_rate: Optional[float] = None
    quantity_gross: Optional[float] = None
    note: Optional[str] = None

class BOMDetailResponse(BOMDetailBase):
    detail_id: int
    bom_id: int # Trả về để biết thuộc header nào

    class Config:
        from_attributes = True