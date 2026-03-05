from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class Employee(Base):
    __tablename__ = "employees"

    employee_id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=True)
    phone = Column(String(20), nullable=True)
    address = Column(String(150), nullable=True)
    position = Column(String(100), nullable=True)
    note = Column(String(150), nullable=True)
    avatar_url = Column(String(255), nullable=True) 

    department_id = Column(Integer, ForeignKey("departments.department_id"))
    
    # [MỚI] Thêm khóa ngoại Tổ nhân viên (nullable=True vì có nhân viên không thuộc tổ nào)
    group_id = Column(Integer, ForeignKey("employee_groups.group_id"), nullable=True)

    # --- QUAN HỆ (RELATIONSHIPS) ---
    department = relationship("Department", back_populates="employees")
    group = relationship("EmployeeGroup", back_populates="employees") # [MỚI]
    
    work_schedules = relationship("WorkSchedule", back_populates="employee")
    user = relationship("User", back_populates="employee", uselist=False)
    weaving_updates = relationship("WeavingProduction", back_populates="updated_by")