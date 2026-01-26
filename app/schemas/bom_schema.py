from pydantic import BaseModel, Field, computed_field
from typing import List, Optional
from datetime import datetime
from app.models.bom_detail import BOMComponentType

# ==========================================
# 1. SCHEMAS CHO BOM DETAIL (CHI TIẾT SỢI)
# (Giữ nguyên logic cũ, chỉ đảm bảo tương thích)
# ==========================================

class BOMDetailBase(BaseModel):
    component_type: BOMComponentType
    # Mặc định = 1 để tránh lỗi validation nếu FE chưa gửi
    material_id: Optional[int] = 1 
    
    threads: int = 0
    yarn_type_name: str  # VD: "03300-PES-WEISS"
    twisted: float = 1.0
    crossweave_rate: float = 0.0 
    actual_length_cm: float = 0.0

    # Tự động tách dtex từ yarn_type_name
    @computed_field
    @property
    def yarn_dtex(self) -> float:
        try:
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
    
    # [THAY ĐỔI] Thêm năm áp dụng, bỏ bom_code/bom_name
    applicable_year: int = Field(..., description="Năm áp dụng (VD: 2026)")
    
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
    # [THAY ĐỔI] Cho phép sửa năm nếu nhập sai (cần validate unique ở service)
    applicable_year: Optional[int] = None 
    
    target_weight_gm: Optional[float] = None
    total_scrap_rate: Optional[float] = None
    total_shrinkage_rate: Optional[float] = None
    is_active: Optional[bool] = None
    
    width_behind_loom: Optional[float] = None
    picks: Optional[int] = None
    
    # Khi update, gửi lại list details để thay thế hoặc update
    details: Optional[List[BOMDetailCreate]] = None

class BOMHeaderResponse(BaseModel):
    """
    Schema output trả về cho Client (API Response).
    """
    bom_id: int
    product_id: int
    
    # [THAY ĐỔI] Trả về năm thay vì code/name
    applicable_year: int
    
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

    # [TIỆN ÍCH] Tạo tên hiển thị tự động cho Frontend
    @computed_field
    def display_name(self) -> str:
        return f"BOM Năm {self.applicable_year}"

    class Config:
        from_attributes = True