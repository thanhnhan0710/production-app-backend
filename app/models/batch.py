import enum
from typing import TYPE_CHECKING, Optional, cast

from sqlalchemy import Column, Integer, String, Date, ForeignKey, Enum, Boolean, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base

# Import các model liên quan để type checking và casting
if TYPE_CHECKING:
    from app.models.material_receipt import MaterialReceiptDetail, MaterialReceipt
    from app.models.supplier import Supplier

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
    
    # --- KHÔNG CẦN THÊM supplier_id NỮA ---
    
    manufacture_date = Column(Date, nullable=True) 
    expiry_date = Column(Date, nullable=True)      
    origin_country = Column(String(50), nullable=True) 
    location = Column(String(10), nullable=True, comment="Vị trí kho/Bin code")

    receipt_detail_id = Column(Integer, ForeignKey("material_receipt_details.detail_id"), nullable=True)
    
    qc_status = Column(Enum(BatchQCStatus), default=BatchQCStatus.PENDING)
    qc_note = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    # Relationships
    material = relationship("Material")

    receipt_detail = relationship(
        "MaterialReceiptDetail", 
        lazy="joined", 
        innerjoin=False
    )
    # [MỚI] Thuộc tính ảo 'supplier'
    # Giúp Pydantic nhìn thấy field 'supplier' dù không có cột trong DB
    @property
    def supplier(self) -> Optional["Supplier"]:
        try:
            # Đi từ Batch -> Detail -> Header (Receipt) -> PO Header -> VENDOR
            if (self.receipt_detail and 
                self.receipt_detail.header and 
                self.receipt_detail.header.po_header):
                
                # SỬA TẠI ĐÂY: Dùng .vendor thay vì .supplier
                return self.receipt_detail.header.po_header.vendor 
                
        except AttributeError:
            pass
        return None