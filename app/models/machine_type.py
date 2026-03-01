from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class MachineType(Base):
    __tablename__ = "machine_types"

    machine_type_id = Column(Integer, primary_key=True, index=True)
    type_name = Column(String(100), nullable=False, unique=True)
    description = Column(String(255), nullable=True)

    # Relationship ngược lại bảng machines (Sử dụng string "Machine" để tránh lỗi import vòng)
    machines = relationship("Machine", back_populates="machine_type")