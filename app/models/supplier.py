import enum
from sqlalchemy import Column, Integer, String, Boolean, Text, Enum
from sqlalchemy.orm import relationship
from app.db.base_class import Base

# 1. Định nghĩa các loại hình nguồn gốc
class SupplierOriginType(str, enum.Enum):
    DOMESTIC = "Domestic"   # Trong nước
    IMPORT = "Import"       # Nhập khẩu

# 2. Định nghĩa loại tiền tệ
class CurrencyType(str, enum.Enum):
    VND = "VND"
    USD = "USD"
    CNY = "CNY" # Thêm Nhân dân tệ nếu nhập từ Trung Quốc
    EUR = "EUR"

# 3. === CẬP NHẬT MỚI: Định nghĩa Điều khoản thanh toán ===
# Đây là các điều khoản phổ biến nhất trong ngành dệt may/nhập khẩu
class PaymentTermType(str, enum.Enum):
    TT = "T/T"              # Telegraphic Transfer (Chuyển tiền bằng điện)
    LC = "L/C"              # Letter of Credit (Thư tín dụng - Quan trọng cho nhập khẩu)
    NET_30 = "Net 30"       # Thanh toán sau 30 ngày kể từ ngày Invoice
    NET_45 = "Net 45"       # Thanh toán sau 45 ngày
    NET_60 = "Net 60"       # Thanh toán sau 60 ngày
    COD = "COD"             # Cash on Delivery (Tiền mặt khi giao hàng)
    IMMEDIATE = "Immediate" # Thanh toán ngay khi đặt hàng

class Supplier(Base):
    __tablename__ = "suppliers"

    supplier_id = Column(Integer, primary_key=True, index=True)
    supplier_name = Column(String(255), nullable=False)
    short_name = Column(String(50), nullable=True)

    origin_type = Column(Enum(SupplierOriginType), nullable=True)
    country = Column(String(100), nullable=True) # VD: VN, CN, KR, TW
    
    currency_default = Column(
        Enum(CurrencyType), 
        default=CurrencyType.VND, 
        nullable=True
    )

    # === CẬP NHẬT TẠI ĐÂY: Thêm trường Payment Term ===
    payment_term = Column(
        Enum(PaymentTermType), 
        default=PaymentTermType.NET_30,
        nullable=True,
        comment="Điều khoản thanh toán mặc định (T/T, L/C, Net 30...)"
    )

    tax_code = Column(String(50), nullable=True)
    contact_person = Column(String(100), nullable=True)
    
    # Email: Unique và Index để tránh trùng lặp và tìm kiếm nhanh
    email = Column(String(100), unique=True, index=True, nullable=False)
    
    address = Column(Text, nullable=True)
    lead_time_days = Column(Integer, default=7, comment="Thời gian giao hàng trung bình (ngày)")
    is_active = Column(Boolean, default=True)
