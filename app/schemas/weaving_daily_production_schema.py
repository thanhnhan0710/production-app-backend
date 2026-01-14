from pydantic import BaseModel, Field, ConfigDict
from datetime import date
from typing import Optional

# ==========================================
# 1. SCHEMA PHỤ CHO SẢN PHẨM (Để nhúng vào kết quả)
# ==========================================
class ProductSimpleSchema(BaseModel):
    """Schema rút gọn của Product chỉ lấy các thông tin cần hiển thị báo cáo"""
    product_id: int
    item_code: str  # Mã sản phẩm (Quan trọng nhất)
    note: Optional[str] = None
    image_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# 2. SCHEMA CHO SẢN LƯỢNG DỆT (WeavingDailyProduction)
# ==========================================

class WeavingProductionBase(BaseModel):
    date: date
    total_meters: float = 0.0
    total_kg: float = 0.0
    active_machine_lines: int = 0

class WeavingProductionCreate(WeavingProductionBase):
    """Dùng khi tạo mới (thường là tính toán từ service, ít khi nhập tay)"""
    product_id: int

class WeavingProductionUpdate(BaseModel):
    """Dùng khi muốn sửa tay số liệu (nếu cần)"""
    total_meters: Optional[float] = None
    total_kg: Optional[float] = None
    active_machine_lines: Optional[int] = None

class WeavingProductionResponse(WeavingProductionBase):
    """Schema trả về cho Frontend (Có kèm thông tin sản phẩm)"""
    id: int
    product_id: int
    
    # [QUAN TRỌNG] Nhúng object Product vào đây
    # Khi query SQLAlchemy, dùng .options(joinedload(WeavingDailyProduction.product))
    product: Optional[ProductSimpleSchema] = None 

    # Nếu bạn muốn làm phẳng dữ liệu (Flatten) để dễ hiển thị lên Table (DataGrid)
    # Bạn có thể dùng @computed_field hoặc để Frontend tự xử lý object 'product' ở trên.
    # Dưới đây là ví dụ nếu muốn lấy riêng item_code ra ngoài:
    # @property
    # def product_code(self) -> str:
    #     return self.product.item_code if self.product else "N/A"

    model_config = ConfigDict(from_attributes=True)