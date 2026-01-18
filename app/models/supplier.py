import enum
from sqlalchemy import Column, Integer, String, Boolean, Text, Enum
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class SupplierOriginType(str, enum.Enum):
    DOMESTIC = "Domestic"
    IMPORT = "Import"

class CurrencyType(str, enum.Enum):
    VND = "VND"
    USD = "USD"

# 1. Định nghĩa các Enum (Trạng thái/Loại)
# Kế thừa str để khi serialize ra JSON (Pydantic) nó tự hiểu là string
class SupplierOriginType(str, enum.Enum):
    DOMESTIC = "Domestic"  # Trong nước
    IMPORT = "Import"      # Nhập khẩu

class CurrencyType(str, enum.Enum):
    VND = "VND"
    USD = "USD"

# 2. Model Supplier
class Supplier(Base):
    __tablename__ = "suppliers"

    # --- Khóa chính ---
    supplier_id = Column(Integer, primary_key=True, index=True)
<<<<<<< HEAD

    # --- Thông tin định danh ---
    supplier_name = Column(String(255), nullable=False)
    short_name = Column(String(50), nullable=True)

    # --- Phân loại (Dùng Enum) ---
    # Map với: OriginType VARCHAR(20) CHECK (OriginType IN ('Domestic', 'Import'))
    origin_type = Column(Enum(SupplierOriginType), nullable=True)

    country = Column(String(100), nullable=True) # VD: VN, KR, CN

    # --- Tài chính (Dùng Enum) ---
    # Map với: CurrencyDefault VARCHAR(3) DEFAULT 'VND'
    # Lưu ý: Set default bằng giá trị Enum (CurrencyType.VND)
    currency_default = Column(
        Enum(CurrencyType), 
        default=CurrencyType.VND, 
        nullable=True
    )

    tax_code = Column(String(50), nullable=True)

    # --- Liên hệ ---
    contact_person = Column(String(100), nullable=True)
    email = Column(String(100), unique=True, index=True, nullable=False)
    address = Column(Text, nullable=True)

    # --- Vận hành ---
    lead_time_days = Column(Integer, default=7)
    is_active = Column(Boolean, default=True)

    # --- Quan hệ ---
=======
    supplier_name = Column(String(255), nullable=False)
    short_name = Column(String(50), nullable=True)

    origin_type = Column(Enum(SupplierOriginType), nullable=True)
    country_code = Column(String(100), nullable=True)
    
    currency_default = Column(
        Enum(CurrencyType), 
        default=CurrencyType.VND, 
        nullable=True
    )

    tax_code = Column(String(50), nullable=True)
    contact_person = Column(String(100), nullable=True)
    
    # === CẬP NHẬT TẠI ĐÂY ===
    # Thêm unique=True (duy nhất) và index=True (tối ưu tìm kiếm)
    # Sửa nullable=False (bắt buộc phải có)
    email = Column(String(100), unique=True, index=True, nullable=False)
    
    address = Column(Text, nullable=True)
    lead_time_days = Column(Integer, default=7)
    is_active = Column(Boolean, default=True)

>>>>>>> c468be65d7388abd40a800c84aa27cfe56d2c0d3
    yarns = relationship("Yarn", back_populates="supplier")