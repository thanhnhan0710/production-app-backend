from pydantic import BaseModel, Field, computed_field
from typing import List, Optional
from datetime import datetime
from app.models.bom_detail import BOMComponentType

# ==========================================
# 1. SCHEMAS CHO BOM DETAIL (CHI TIẾT SỢI)
# ==========================================

class BOMDetailBase(BaseModel):
    component_type: BOMComponentType
    # Mặc định = 1 để tránh lỗi validation nếu FE chưa gửi, logic Service sẽ xử lý sau
    material_id: Optional[int] = 1 
    
    threads: int = 0
    yarn_type_name: str  # VD: "03300-PES-WEISS"
    twisted: float = 1.0
    crossweave_rate: float = 0.0  # Đơn vị: 0.04 thay vì 4%
    actual_length_cm: float = 0.0

    # Tự động tách dtex từ yarn_type_name (Logic hiển thị & tính toán sơ bộ)
    @computed_field
    @property
    def yarn_dtex(self) -> float:
        try:
            # Lấy 5 ký tự đầu và đổi sang số
            if not self.yarn_type_name or len(self.yarn_type_name) < 5:
                return 0.0
            return float(self.yarn_type_name[:5])
        except (ValueError, IndexError, AttributeError):
            return 0.0

class BOMDetailCreate(BOMDetailBase):
    """Schema dùng để tạo mới chi tiết sợi"""
    pass

class BOMDetailRead(BOMDetailBase):
    """Schema dùng để trả về dữ liệu chi tiết sợi (bao gồm kết quả tính toán)"""
    detail_id: int
    bom_id: int
    
    # Các trường kết quả tính toán từ Service
    weight_per_yarn_gm: float
    actual_weight_cal: float
    weight_percentage: float
    bom_gm: float

    class Config:
        from_attributes = True

# ==========================================
# 2. SCHEMAS CHO BOM HEADER (THÔNG TIN CHUNG)
# ==========================================

class BOMHeaderCreate(BaseModel):
    """Schema input khi tạo BOM mới"""
    product_id: int
    bom_code: str
    bom_name: Optional[str] = None
    target_weight_gm: float
    
    # Các tỷ lệ hao hụt chung
    total_scrap_rate: float = 0.0
    total_shrinkage_rate: float = 0.0
    
    # Thông số kỹ thuật máy
    width_behind_loom: Optional[float] = 0.0
    picks: Optional[int] = 0
    
    # Danh sách chi tiết sợi đi kèm
    details: List[BOMDetailCreate]

class BOMHeaderUpdate(BaseModel):
    """Schema input khi cập nhật BOM"""
    bom_name: Optional[str] = None
    target_weight_gm: Optional[float] = None
    total_scrap_rate: Optional[float] = None
    total_shrinkage_rate: Optional[float] = None
    is_active: Optional[bool] = None
    
    width_behind_loom: Optional[float] = None
    picks: Optional[int] = None
    
    # Khi update, thường gửi lại toàn bộ danh sách sợi để tính toán lại từ đầu
    details: Optional[List[BOMDetailCreate]] = None

class BOMHeaderResponse(BaseModel):
    """
    Schema output trả về cho Client (API Response).
    Khắc phục lỗi ImportError: cannot import name 'BOMHeaderResponse'
    """
    bom_id: int
    product_id: int
    bom_code: str
    bom_name: Optional[str] = None
    
    target_weight_gm: float
    total_scrap_rate: float
    total_shrinkage_rate: float
    
    width_behind_loom: Optional[float]
    picks: Optional[int]
    
    version: int
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Relationship: Trả về kèm danh sách chi tiết
    bom_details: List[BOMDetailRead] = []

    class Config:
        from_attributes = True