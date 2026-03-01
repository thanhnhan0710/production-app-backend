from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class Area(Base):
    __tablename__ = "areas"

    area_id = Column(Integer, primary_key=True, index=True)
    area_name = Column(String(100), nullable=False, unique=True)
    description = Column(String(255), nullable=True)

    # Nối với bảng machines (Sử dụng string "Machine" để tránh lỗi import vòng)
    machines = relationship("Machine", back_populates="area")
    
