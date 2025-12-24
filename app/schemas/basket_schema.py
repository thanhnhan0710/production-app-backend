from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class BasketStatus(str, Enum):
    READY = "READY"         # Sẵn sàng sử dụng
    IN_USE = "IN_USE"       # Đang chứa hàng
    HOLDING = "HOLDING"     # Đang giữ hàng
    DAMAGED = "DAMAGED"     # Hư hỏng


# BASE SCHEMA (Các trường chung)
class BasketBase(BaseModel):
    basket_code: str = Field(..., max_length=50, description="Mã rổ (Duy nhất)")
    tare_weight: float = Field(..., gt=0, description="Trọng lượng bì của rổ (kg). Phải lớn hơn 0")
    supplier: Optional[str] = Field(None, max_length=100, description="Nhà cung cấp")
    status: BasketStatus = Field(default=BasketStatus.READY, description="Trạng thái hiện tại")
    note: Optional[str] = None

# =======================
# CREATE SCHEMA (Dùng khi tạo mới)

class BasketCreate(BasketBase):
    pass
    # Kế thừa toàn bộ từ Base vì khi tạo mới cần tất cả thông tin trên.
    # ID sẽ tự sinh.

# =======================
# UPDATE SCHEMA (Dùng khi chỉnh sửa)
# =======================
# Tất cả các trường đều là Optional vì người dùng có thể chỉ sửa 1 trường
class BasketUpdate(BaseModel):
    basket_code: Optional[str] = Field(None, max_length=50)
    tare_weight: Optional[float] = Field(None, gt=0)
    supplier: Optional[str] = None
    status: Optional[BasketStatus] = None
    note: Optional[str] = None

# =======================
# RESPONSE SCHEMA (Trả về Client)
# =======================
class BasketResponse(BasketBase):
    basket_id: int

    class Config:
        from_attributes = True  # Quan trọng: Để map từ SQLAlchemy model sang Pydantic

# =======================
# SEARCH/FILTER SCHEMA (Bonus)
# =======================
# Dùng cho API search nếu cần
class BasketFilter(BaseModel):
    basket_code: Optional[str] = None
    status: Optional[BasketStatus] = None
    supplier: Optional[str] = None
    min_weight: Optional[float] = None
    max_weight: Optional[float] = None