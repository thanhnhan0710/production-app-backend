from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base

class Employee(Base):
    __tablename__ = "employees"

    employee_id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    phone = Column(String(20), nullable=True)
    address=Column(String(150), nullable=True)
    position= Column(String(100), nullable=True)
    department_id = Column(Integer, ForeignKey("departments.department_id"))
    note=Column(String(150), nullable=True)

    # Quan hệ n-1: Nhân viên thuộc về một phòng ban
    department = relationship("Department", back_populates="employees")