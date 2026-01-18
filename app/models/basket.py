import enum
from sqlalchemy import Column, Integer, String, Float, Text, Enum
from app.db.base_class import Base

# 1. Định nghĩa các trạng thái của Rổ (để tránh nhập sai chính tả)
class BasketStatus(str, enum.Enum):
    READY = "READY"         # Sẵn sàng sử dụng
    IN_USE = "IN_USE"       # Đang chứa hàng (trong chuyền)
    HOLDING = "HOLDING"     # Đang lưu kho/giữ hàng
    DAMAGED = "DAMAGED"     # Hư hỏng (cần sửa chữa/loại bỏ)

# 2. Model Bảng Rổ
class Basket(Base):
    __tablename__ = "baskets"

    basket_id = Column(Integer, primary_key=True, index=True)
    basket_code = Column(String(50), unique=True, index=True, nullable=False) 
    tare_weight = Column(Float, nullable=False)
    
    # Trạng thái (Dùng Enum đã định nghĩa ở trên)
    # default là READY (Sẵn sàng)
    status = Column(Enum(BasketStatus), default=BasketStatus.READY, nullable=False)
    note = Column(Text, nullable=True) # Ghi chú