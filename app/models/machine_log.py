from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from app.db.base_class import Base

class MachineLog(Base):
    __tablename__ = "machine_logs"

    id = Column(Integer, primary_key=True, index=True)
    machine_id = Column(Integer, ForeignKey("machines.machine_id"), nullable=False)
    
    status = Column(String(50), nullable=False) # RUNNING, STOPPED, MAINTENANCE...
    
    start_time = Column(DateTime, default=func.now(), nullable=False)
    end_time = Column(DateTime, nullable=True) # Null nghĩa là "Hiện tại đang ở trạng thái này"
    
    reason = Column(Text, nullable=True)       # Lý do dừng máy
    image_url = Column(String(500), nullable=True) # Link ảnh sự cố