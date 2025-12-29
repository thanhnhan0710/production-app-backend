from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.db.base import Base

class Department(Base):
    __tablename__ = "departments"

    department_id = Column(Integer, primary_key=True, index=True)
    department_name = Column(String(100), unique=True, index=True, nullable=False)
    description = Column(String(255), nullable=True)

    # Quan hệ 1-n: Một phòng ban có nhiều nhân viên
    employees = relationship("Employee", back_populates="department")
