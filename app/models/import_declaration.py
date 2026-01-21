import enum
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Date, Enum, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base

# 1. Định nghĩa Mã loại hình nhập khẩu (Theo chuẩn VNACCS/VCIS Việt Nam)
class ImportType(str, enum.Enum):
    E31 = "E31" # Nhập nguyên liệu sản xuất xuất khẩu (SXXK) - Quan trọng nhất
    E21 = "E21" # Nhập nguyên liệu gia công cho thương nhân nước ngoài
    A11 = "A11" # Nhập kinh doanh tiêu dùng (Có nộp thuế)
    A12 = "A12" # Nhập kinh doanh sản xuất
    G11 = "G11" # Tạm nhập tái xuất

# 2. Bảng Header: Thông tin chung tờ khai
class ImportDeclaration(Base):
    __tablename__ = "import_declarations"

    id = Column(Integer, primary_key=True, index=True)
    
    # Số tờ khai (Bắt buộc, Duy nhất)
    declaration_no = Column(String(50), unique=True, index=True, nullable=False)
    
    declaration_date = Column(Date, nullable=False) # Ngày đăng ký tờ khai
    
    # Loại hình: Quyết định logic thanh khoản sau này
    type_of_import = Column(Enum(ImportType), nullable=False, default=ImportType.E31)
    
    # Chứng từ vận tải & Thương mại
    bill_of_lading = Column(String(50), nullable=True) # Số vận đơn (B/L)
    invoice_no = Column(String(50), nullable=True)     # Số Invoice
    
    # Tổng quan
    total_tax_amount = Column(Float, default=0.0)      # Tổng thuế (nếu có)
    note = Column(Text, nullable=True)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    # Relationships
    details = relationship("ImportDeclarationDetail", back_populates="declaration", cascade="all, delete-orphan")

# 3. Bảng Detail: Chi tiết hàng hóa trong tờ khai
# Tại sao cần bảng này? Vì 1 tờ khai có thể nhập Sợi 1000D, Sợi 500D và Sợi biên cùng lúc.
class ImportDeclarationDetail(Base):
    __tablename__ = "import_declaration_details"

    detail_id = Column(Integer, primary_key=True, index=True)
    
    declaration_id = Column(Integer, ForeignKey("import_declarations.id"), nullable=False)
    
    # Liên kết với Vật tư
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False)
    
    # (Tùy chọn) Liên kết với PO để biết hàng này về của đơn mua nào
    po_detail_id = Column(Integer, ForeignKey("purchase_order_details.detail_id"), nullable=True)
    
    quantity = Column(Float, nullable=False) # Số lượng trên tờ khai (Kg)
    unit_price = Column(Float, nullable=False) # Đơn giá khai báo (USD)
    
    hs_code_actual = Column(String(20), nullable=True) # HS Code thực tế áp trên tờ khai (có thể khác trong Master)
    
    # Relationships
    declaration = relationship("ImportDeclaration", back_populates="details")
    material = relationship("Material")