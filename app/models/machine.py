import enum
from sqlalchemy import Column, Integer, String, Enum
from app.db.base_class import Base
from sqlalchemy.orm import relationship

# 1. Định nghĩa các trạng thái của Máy
class MachineStatus(str, enum.Enum):
    STOPPED = "STOPPED"          
    RUNNING = "RUNNING"          
    MAINTENANCE = "MAINTENANCE"  
    SPINNING = "SPINNING"       

# 2. [MỚI] Định nghĩa các Khu vực (Area)
class MachineArea(str, enum.Enum):
    SECTION_A = "Khu A"
    SECTION_B = "Khu B"
    SECTION_C = "Khu C"
    # Có thể thêm SECTION_D = "Khu D" sau này nếu mở rộng xưởng

# 3. Model Bảng Machine
class Machine(Base):
    __tablename__ = "machines"

    machine_id = Column(Integer, primary_key=True, index=True)
    machine_name = Column(String(100), nullable=False)

    total_lines = Column(Integer, nullable=True)
    purpose = Column(String(255), nullable=True)

    # Cột trạng thái (Enum)
    status = Column(
        Enum(MachineStatus), 
        default=MachineStatus.STOPPED, 
        nullable=False
    )

    # [MỚI] Cột khu vực (Enum)
    area = Column(
        Enum(MachineArea), 
        nullable=True, 
        index=True 
    )

    weaving_productions = relationship("WeavingProduction", back_populates="machine")