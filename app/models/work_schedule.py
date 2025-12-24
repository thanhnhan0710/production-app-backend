from sqlalchemy import Column, Integer, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base

class WorkSchedule(Base):
    __tablename__ = "work_schedules"

    id = Column(Integer, primary_key=True, index=True)         
    work_date = Column(Date, nullable=False, index=True)        
    
    # Khóa ngoại liên kết
    employee_id = Column(Integer, ForeignKey("employees.employee_id"), nullable=False) 
    shift_id = Column(Integer, ForeignKey("shifts.shift_id"), nullable=False)       

    # Thiết lập quan hệ (Relationships) để truy vấn ngược
    employee = relationship("Employee", back_populates="work_schedules")
    shift = relationship("Shift", back_populates="work_schedules")