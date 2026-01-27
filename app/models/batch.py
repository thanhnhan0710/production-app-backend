import enum
from typing import TYPE_CHECKING, Optional, cast

from sqlalchemy import Column, Integer, String, Date, ForeignKey, Enum, Boolean, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base

# [FIX 1] Import cast từ typing
if TYPE_CHECKING:
    from app.models.material_receipt import MaterialReceiptDetail, MaterialReceipt

class BatchQCStatus(str, enum.Enum):
    PENDING = "Pending"
    PASS = "Pass"
    FAIL = "Fail"
    EXPIRED = "Expired"

class Batch(Base):
    __tablename__ = "batches"

    batch_id = Column(Integer, primary_key=True, index=True)
    internal_batch_code = Column(String(50), unique=True, index=True, nullable=False)
    supplier_batch_no = Column(String(100), index=True, nullable=False)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False)
    
    manufacture_date = Column(Date, nullable=True) 
    expiry_date = Column(Date, nullable=True)      
    origin_country = Column(String(50), nullable=True) 
    
    # [YÊU CẦU 2] Thêm vị trí kho (Max 10 ký tự)
    location = Column(String(10), nullable=True, comment="Vị trí kho/Bin code")

    # Liên kết khóa ngoại
    receipt_detail_id = Column(Integer, ForeignKey("material_receipt_details.detail_id"), nullable=True)
    
    qc_status = Column(Enum(BatchQCStatus), default=BatchQCStatus.PENDING)
    qc_note = Column(String(255), nullable=True)
    
    is_active = Column(Boolean, default=True)
    note = Column(Text, nullable=True)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    # Relationships
    material = relationship("Material")
    
    # [FIX 2] Khai báo relationship bình thường
    # Lưu ý: Việc tách if TYPE_CHECKING riêng cho biến receipt_detail đôi khi làm Pylance bị rối 
    # trong context của SQLAlchemy model. Ta sẽ xử lý bằng cast bên dưới.
    receipt_detail = relationship("MaterialReceiptDetail", lazy="joined")

    # [YÊU CẦU 1] Property ảo lấy số phiếu nhập
    @property
    def receipt_number(self) -> Optional[str]:
        # 1. Kiểm tra detail có tồn tại không
        if not self.receipt_detail:
            return None
        
        # [FIX 3] Ép kiểu tường minh (Explicit Casting)
        # Chỉ chạy khi TYPE_CHECKING để không ảnh hưởng hiệu năng runtime
        # Giúp IDE biết chính xác 'detail' và 'header' là class nào
        if TYPE_CHECKING:
            detail = cast("MaterialReceiptDetail", self.receipt_detail)
            if detail.header:
                header = cast("MaterialReceipt", detail.header)
                return header.receipt_number
        
        # Logic chạy thực tế (Runtime)
        # Vì Python là dynamic type nên đoạn này vẫn chạy tốt dù IDE không gợi ý
        try:
            return self.receipt_detail.header.receipt_number
        except AttributeError:
            return None