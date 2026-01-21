from pydantic import BaseModel, EmailStr, Field
from typing import Optional
# Import Enum từ file model
# Đảm bảo bạn đã export PaymentTermType trong __init__.py của models hoặc import trực tiếp
from app.models.supplier import SupplierOriginType, CurrencyType, PaymentTermType

# Class cơ sở chứa các trường chung
class SupplierBase(BaseModel):
    supplier_name: str = Field(..., max_length=255)
    short_name: Optional[str] = Field(None, max_length=50)
    
    # Thay Literal bằng Enum để đồng bộ với Database và hiển thị Dropdown trên Swagger
    origin_type: Optional[SupplierOriginType] = None
    
    country: Optional[str] = Field(None, max_length=100)
    
    # Mặc định dùng Enum.VND
    currency_default: Optional[CurrencyType] = CurrencyType.VND

    # === CẬP NHẬT: Thêm trường Payment Term ===
    # Mặc định là Net 30 theo DB, cho phép null
    payment_term: Optional[PaymentTermType] = PaymentTermType.NET_30
    
    contact_person: Optional[str] = Field(None, max_length=100)
    
    email: Optional[EmailStr] = None

    tax_code: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = None
    
    lead_time_days: Optional[int] = 7
    is_active: Optional[bool] = True

# Class dùng khi tạo mới (Create) - Giống Base
class SupplierCreate(SupplierBase):
    pass

# Class dùng khi cập nhật (Update) - Tất cả các trường đều là Optional
class SupplierUpdate(BaseModel):
    supplier_name: Optional[str] = Field(None, max_length=255)
    short_name: Optional[str] = Field(None, max_length=50)
    
    origin_type: Optional[SupplierOriginType] = None
    country: Optional[str] = Field(None, max_length=100)
    currency_default: Optional[CurrencyType] = None
    
    # Cho phép update payment_term
    payment_term: Optional[PaymentTermType] = None
    
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