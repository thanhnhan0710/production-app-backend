import enum
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.db.base_class import Base

# 1. Định nghĩa loại thành phần trong cấu trúc dệt (Nằm chung với bảng sử dụng nó)
class BOMComponentType(str, enum.Enum):
    WARP = "Warp"       # Sợi dọc (Đi theo chiều dài dây)
    WEFT = "Weft"       # Sợi ngang (Đi theo chiều rộng dây)
    BINDER = "Binder"   # Sợi biên/khóa (Giữ mép dây)
    DYE = "Dye"         # Hóa chất nhuộm (Nếu có nhuộm)

# 3. Bảng BOM Detail (Chi tiết nguyên liệu)
class BOMDetail(Base):
    __tablename__ = "bom_details"

    detail_id = Column(Integer, primary_key=True, index=True)
    
    # Liên kết về Header
    bom_id = Column(Integer, ForeignKey("bom_headers.bom_id"), nullable=False)
    
    # Liên kết về Vật tư (Sợi)
    # Giả định bảng 'materials' có khoá chính là 'id'
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False)
    
    # Loại sợi (Dọc/Ngang) - Rất quan trọng cho bộ phận Kế hoạch sản xuất
    component_type = Column(Enum(BOMComponentType), nullable=False)
    
    # --- CÁC TRƯỜNG ĐỊNH MỨC KỸ THUẬT ---
    
    # 1. Số lượng sợi (Total Ends) - Chỉ dùng cho Sợi Dọc
    # VD: Dây đai rộng 5cm cần 200 sợi dọc chạy song song
    number_of_ends = Column(Integer, nullable=True, default=0, comment="Tổng số sợi dọc")
    
    # 2. Định mức tiêu hao (Consumption)
    # VD: Cần 15g sợi cho 1 mét dây thành phẩm
    quantity_standard = Column(Float, nullable=False, comment="Số lượng chuẩn (g/m)")
    
    # 3. Tỷ lệ hao hụt (Wastage)
    # Trong dệt, hao hụt do nối sợi, đầu mấu, dệt thử máy rất cao (2-5%)
    wastage_rate = Column(Float, default=0.0, comment="Tỷ lệ hao hụt (%)")
    
    # 4. Tổng nhu cầu (Gross Quantity)
    # Gross = Standard * (1 + Wastage/100)
    quantity_gross = Column(Float, nullable=False, comment="Tổng lượng cần xuất kho bao gồm hao hụt")

    # Ghi chú kỹ thuật (VD: Sợi này nằm ở mép trái)
    note = Column(String(200), nullable=True)

    # Relationships
    header = relationship("BOMHeader", back_populates="bom_details")
    
    # Giả định Model Material đã được define ở file khác
    material = relationship("Material")