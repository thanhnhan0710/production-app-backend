import enum
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Enum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base

# Enum kết quả kiểm tra
class IQCResultStatus(str, enum.Enum):
    PASS = "Pass"
    FAIL = "Fail"
    PENDING = "Pending"

class IQCResult(Base):
    __tablename__ = "iqc_results"

    test_id = Column(Integer, primary_key=True, index=True)
    
    # Liên kết lô hàng cần test
    batch_id = Column(Integer, ForeignKey("batches.batch_id"), nullable=False)
    
    test_date = Column(DateTime, default=func.now())
    tester_name = Column(String(100), nullable=True) # Người kiểm tra
    
    # --- CÁC CHỈ SỐ KỸ THUẬT (QUAN TRỌNG) ---
    tensile_strength = Column(Float, nullable=True) # Lực kéo đứt (Newton/Kgf)
    elongation = Column(Float, nullable=True)       # Độ giãn (%)
    color_fastness = Column(Float, nullable=True)   # Độ bền màu (Scale 1-5)
    
    # Kết quả cuối cùng
    final_result = Column(Enum(IQCResultStatus), default=IQCResultStatus.PENDING)
    
    note = Column(Text, nullable=True)
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    # Relationships
    batch = relationship("Batch")