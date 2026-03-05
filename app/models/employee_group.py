from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class EmployeeGroup(Base):
    __tablename__ = "employee_groups"

    group_id = Column(Integer, primary_key=True, index=True)
    group_name = Column(String(100), unique=True, index=True, nullable=False)
    description = Column(String(255), nullable=True)
    
    # Tổ thường thuộc về 1 Phòng ban/Xưởng cụ thể
    department_id = Column(Integer, ForeignKey("departments.department_id"), nullable=True)

    # --- QUAN HỆ (RELATIONSHIPS) ---
    # 1 Tổ thuộc về 1 Phòng ban
    department = relationship("Department", back_populates="groups")
    
    # 1 Tổ có nhiều Nhân viên
    employees = relationship("Employee", back_populates="group")