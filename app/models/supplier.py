import enum
from sqlalchemy import Column, Integer, String, Boolean, Text, Enum
from sqlalchemy.orm import relationship
from app.db.base_class import Base

# 1. Định nghĩa các Enum (Chỉ giữ lại 1 bản định nghĩa)
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

    # --- Thông tin định danh ---
    supplier_name = Column(String(255), nullable=False)
    short_name = Column(String(50), nullable=True)

    # --- Phân loại ---
    origin_type = Column(Enum(SupplierOriginType), nullable=True)
    
    # Sử dụng country_code theo bản mới nhất
    country_code = Column(String(100), nullable=True)

    # --- Tài chính ---
    currency_default = Column(
        Enum(CurrencyType), 
        default=CurrencyType.VND, 
        nullable=True
    )

    tax_code = Column(String(50), nullable=True)
    contact_person = Column(String(100), nullable=True)

    # --- Liên hệ ---
    # LƯU Ý: Ở bản mới nhất trên Git, bạn đang để nullable=False (Bắt buộc nhập).
    # Nếu bạn muốn Email là TÙY CHỌN (như trong Schema Pydantic), hãy sửa thành nullable=True.
    email = Column(String(100), unique=True, index=True, nullable=False)

    address = Column(Text, nullable=True)

    # --- Vận hành ---
    lead_time_days = Column(Integer, default=7)
    is_active = Column(Boolean, default=True)

    # --- Quan hệ ---
    yarns = relationship("Yarn", back_populates="supplier")