from pydantic import BaseModel, EmailStr, Field
from typing import Optional
# Import Enum từ file model (hoặc nơi bạn định nghĩa common enums)
# Giả sử file model nằm tại app.models.supplier
from app.models.supplier import SupplierOriginType, CurrencyType

# Class cơ sở chứa các trường chung
class SupplierBase(BaseModel):
    supplier_name: str = Field(..., max_length=255)
    short_name: Optional[str] = Field(None, max_length=50)
    
    # Thay Literal bằng Enum để đồng bộ với Database và hiển thị Dropdown trên Swagger
    origin_type: Optional[SupplierOriginType] = None
    
    country: Optional[str] = Field(None, max_length=100)
    
    # Mặc định dùng Enum.VND
    currency_default: Optional[CurrencyType] = CurrencyType.VND
    
    contact_person: Optional[str] = Field(None, max_length=100)
    email: EmailStr
    tax_code: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = None
    
    lead_time_days: Optional[int] = 7
    is_active: Optional[bool] = True

# Class dùng khi tạo mới (Create) - Giống Base nhưng có thể validate thêm nếu cần
class SupplierCreate(SupplierBase):
    pass

# Class dùng khi cập nhật (Update) - Tất cả các trường đều là Optional
class SupplierUpdate(BaseModel):
    supplier_name: Optional[str] = Field(None, max_length=255)
    short_name: Optional[str] = Field(None, max_length=50)
    
    # Cho phép update từng trường riêng lẻ
    origin_type: Optional[SupplierOriginType] = None
    country: Optional[str] = Field(None, max_length=100)
    currency_default: Optional[CurrencyType] = None
    
    contact_person: Optional[str] = Field(None, max_length=100)
    email: Optional[EmailStr] = None
    tax_code: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = None
    lead_time_days: Optional[int] = None
    is_active: Optional[bool] = None

# Class dùng để trả về dữ liệu (Response)
class SupplierResponse(SupplierBase):
    supplier_id: int

    class Config:
        # Pydantic v2 dùng from_attributes thay cho orm_mode
        from_attributes = True