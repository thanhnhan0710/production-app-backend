from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class Machine(Base):
    __tablename__ = "machines"

    machine_id = Column(Integer, primary_key=True, index=True)
    machine_name = Column(String(100), nullable=False, unique=True)
    serial_number = Column(String(100), nullable=True)
    
    # Khóa ngoại
    machine_type_id = Column(Integer, ForeignKey("machine_types.machine_type_id"), nullable=True)
    status_id = Column(Integer, ForeignKey("machine_statuses.status_id"), nullable=True)
    
    # [CẬP NHẬT] Đổi từ machine_areas sang areas
    area_id = Column(Integer, ForeignKey("areas.area_id"), nullable=True)

    # Cột phân loại đa hình
    polymorphic_type = Column(String(50), nullable=False)

    __mapper_args__ = {
        "polymorphic_identity": "base_machine",
        "polymorphic_on": polymorphic_type,     
    }

    # Relationships
    machine_type = relationship("MachineType", back_populates="machines")
    status = relationship("MachineStatus", back_populates="machines")
    
    # [CẬP NHẬT] Đổi relationship sang Area
    area = relationship("Area", back_populates="machines")

# BẢNG CON: MÁY DỆT
class WeavingMachine(Machine):
    __tablename__ = "weaving_machines"
    machine_id = Column(Integer, ForeignKey("machines.machine_id", ondelete="CASCADE"), primary_key=True)
    
    total_lines = Column(Integer, nullable=True)
    speed = Column(Integer, nullable=True)
    purpose = Column(String(255), nullable=True)

    __mapper_args__ = {"polymorphic_identity": "weaving_machine"}

    weaving_productions = relationship("WeavingProduction", back_populates="machine")

# BẢNG CON: MÁY NHUỘM
class DyeingMachine(Machine):
    __tablename__ = "dyeing_machines"
    machine_id = Column(Integer, ForeignKey("machines.machine_id", ondelete="CASCADE"), primary_key=True)
    
    capacity_kg = Column(Float, nullable=True)
    max_temperature = Column(Float, nullable=True)

    __mapper_args__ = {"polymorphic_identity": "dyeing_machine"}