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

class Supplier(Base):
    __tablename__ = "suppliers"

    supplier_id = Column(Integer, primary_key=True, index=True)
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

    yarns = relationship("Yarn", back_populates="supplier")