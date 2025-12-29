from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base

class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    
    # Thông tin đăng nhập
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    
    # Thông tin cá nhân
    full_name = Column(String(100), index=True)
    phone_number = Column(String(20), nullable=True)
    
    # Trạng thái & Phân quyền
    is_active = Column(Boolean, default=True)      # Cho phép đăng nhập hay không
    is_superuser = Column(Boolean, default=False)  # Admin hệ thống
    role = Column(String(50), default="staff")     # Ví dụ: admin, manager, staff, worker
    
    # Relationships
    logs = relationship("Log", back_populates="user")