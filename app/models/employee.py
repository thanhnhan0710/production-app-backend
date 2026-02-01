from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base_class import Base # Hoặc app.db.base_class tùy project của bạn

class Employee(Base):
    __tablename__ = "employees"

    employee_id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    phone = Column(String(20), nullable=True)
    address = Column(String(150), nullable=True)
    position = Column(String(100), nullable=True)
    note = Column(String(150), nullable=True)
    
    # --- THÊM TRƯỜNG ẢNH MỚI ---
    # Lưu đường dẫn file (ví dụ: /static/images/avatar_1.jpg) 
    # hoặc URL đầy đủ (ví dụ: https://s3.aws.../avatar.png)
    avatar_url = Column(String(255), nullable=True) 

    department_id = Column(Integer, ForeignKey("departments.department_id"))

    # Quan hệ
    department = relationship("Department", back_populates="employees")
    work_schedules = relationship("WorkSchedule", back_populates="employee")
    user = relationship("User", back_populates="employee", uselist=False)
    weaving_updates = relationship("WeavingProduction", back_populates="updated_by")