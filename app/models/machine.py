import enum
from sqlalchemy import Column, Integer, String, Enum
from app.db.base_class import Base
from sqlalchemy.orm import relationship

class MachineStatus(str, enum.Enum):
    STOPPED = "STOPPED"          
    RUNNING = "RUNNING"          
    MAINTENANCE = "MAINTENANCE"  
    SPINNING = "SPINNING"
    YARNOUT ="YARNOUT"    

class MachineArea(str, enum.Enum):
    SECTION_A = "Khu A"
    SECTION_B = "Khu B"
    SECTION_C = "Khu C"

class Machine(Base):
    __tablename__ = "machines"

    machine_id = Column(Integer, primary_key=True, index=True)
    machine_name = Column(String(100), nullable=False, unique=True) # Nên set unique để tránh trùng tên máy

    total_lines = Column(Integer, nullable=True)
    purpose = Column(String(255), nullable=True)
    
    # [MỚI THÊM] Số seri và Tốc độ
    serial_number = Column(String(100), nullable=True)
    speed = Column(Integer, nullable=True)

    status = Column(
        Enum(MachineStatus), 
        default=MachineStatus.STOPPED, 
        nullable=False
    )

    area = Column(
        Enum(MachineArea), 
        nullable=True, 
        index=True 
    )

    weaving_productions = relationship("WeavingProduction", back_populates="machine")