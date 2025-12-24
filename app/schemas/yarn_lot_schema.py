from pydantic import BaseModel, Field
from datetime import date
from typing import Optional

# =======================
# DEPENDENCY SCHEMAS (Schemas phụ thuộc)
# =======================

# Dùng để hiển thị thông tin tóm tắt của nhân viên (Driver, Receiver, Updater)
class EmployeeShort(BaseModel):
    employee_id: int
    full_name: str

    class Config:
        from_attributes = True

# Dùng để hiển thị thông tin tóm tắt của loại sợi (Yarn)
# (Giả sử bạn có bảng Yarn, nếu chưa có schema Yarn thì dùng cái này tạm)
class YarnShort(BaseModel):
    yarn_id: int
    name: str # Giả sử bảng yarn có cột name hoặc yarn_name

    class Config:
        from_attributes = True

# =======================
# MAIN SCHEMAS (Yarn Lot)
# =======================

# 1. Base: Chứa các trường chung
class YarnLotBase(BaseModel):
    import_date: date
    total_kg: float
    roll_count: int
    
    warehouse_location: Optional[str] = None
    container_code: Optional[str] = None
    note: Optional[str] = None

# 2. Create: Dùng khi tạo mới (Client gửi lên)
class YarnLotCreate(YarnLotBase):
    lot_code: str = Field(..., max_length=50) # Bắt buộc, max 50 ký tự
    yarn_id: int
    
    receiver_id: int
    updated_by: int
    driver_id: Optional[int] = None # Có thể null

# 3. Update: Dùng khi chỉnh sửa (Tất cả đều là Optional)
class YarnLotUpdate(BaseModel):
    lot_code: Optional[str] = Field(None, max_length=50)
    yarn_id: Optional[int] = None
    import_date: Optional[date] = None
    
    total_kg: Optional[float] = None
    roll_count: Optional[int] = None
    
    warehouse_location: Optional[str] = None
    container_code: Optional[str] = None
    
    driver_id: Optional[int] = None
    receiver_id: Optional[int] = None
    updated_by: Optional[int] = None # Thường update logic sẽ tự lấy user login, nhưng để đây nếu cần
    note: Optional[str] = None

# 4. Response: Dùng để trả về dữ liệu dạng phẳng (Flat data)
class YarnLotResponse(YarnLotBase):
    id: int  # Quan trọng: Phải có ID database trả về
    lot_code: str
    yarn_id: int
    
    driver_id: Optional[int] = None
    receiver_id: int
    updated_by: int

    class Config:
        from_attributes = True

# 5. Detail: Dùng để trả về dữ liệu chi tiết (Bao gồm thông tin nhân viên và sợi)
class YarnLotDetail(YarnLotResponse):
    # Nested objects (lấy từ relationship)
    yarn: Optional[YarnShort] = None
    driver: Optional[EmployeeShort] = None
    receiver: Optional[EmployeeShort] = None
    updater: Optional[EmployeeShort] = None 
    
    # Lưu ý: 'updater' map với relationship updater trong model, 
    # dù cột FK là updated_by