from sqlalchemy import Column, Integer, String
from app.db.base_class import Base
from sqlalchemy.orm import relationship

class Shift(Base):
    __tablename__ = "shifts"

    shift_id = Column(Integer, primary_key=True, index=True)
    shift_name = Column(String(50), nullable=False)
    note = Column(String(255), nullable=True)
    
    work_schedules = relationship("WorkSchedule", back_populates="shift")
    weaving_productions = relationship("WeavingProduction", back_populates="shift")