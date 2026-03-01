from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class MachineStatus(Base):
    __tablename__ = "machine_statuses"

    status_id = Column(Integer, primary_key=True, index=True)
    status_name = Column(String(100), nullable=False, unique=True)
    color_code = Column(String(20), nullable=True)
    description = Column(String(255), nullable=True)

    machines = relationship("Machine", back_populates="status")