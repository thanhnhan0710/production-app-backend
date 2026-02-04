import enum # [MỚI] Import thư viện enum của Python
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Enum # [MỚI] Import Enum của SQLAlchemy
from sqlalchemy.orm import relationship
from app.db.base_class import Base
# from app.models.log import Log # (Giữ nguyên import cũ của bạn)

# 1. Định nghĩa các quyền (Role) cố định
class UserRole(str, enum.Enum):
    ADMIN = "admin"       # Quản trị viên (Toàn quyền)
    MANAGER = "manager"   # Quản lý (Xem báo cáo, duyệt đơn)
    STAFF = "staff"       # Nhân viên (Tạo đơn, xem đơn của mình)
    WORKER="worker"
    WAREHOUSE="warehouse"

class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    
    # Thông tin đăng nhập
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    
    # Thông tin cá nhân
    full_name = Column(String(100), index=True)
    phone_number = Column(String(20), nullable=True)
    
    # Liên kết với bảng Employee
    employee_id = Column(Integer, ForeignKey("employees.employee_id"), nullable=True)
    
    # Trạng thái & Phân quyền
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    
    # [CẬP NHẬT] Thay đổi từ String sang Enum
    # Cũ: role = Column(String(50), default="staff")
    role = Column(Enum(UserRole), default=UserRole.STAFF, nullable=False)
    
    # Relationships
    logs = relationship("Log", back_populates="user")
    employee = relationship("Employee", back_populates="user")