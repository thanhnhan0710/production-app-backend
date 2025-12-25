from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base

class Log(Base):
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True, index=True)
    
    # 1. Ai làm?
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=True)
    
    # 2. Làm gì? (CREATE, UPDATE, DELETE, LOGIN, ERROR...)
    action = Column(String(50), nullable=False, index=True)
    
    # 3. Đối tượng nào? (Ví dụ: "Product", "Order")
    target_type = Column(String(50), nullable=True, index=True)
    
    # 4. ID của đối tượng đó (Ví dụ: Product ID = 10)
    target_id = Column(Integer, nullable=True)
    
    # 5. Chi tiết thay đổi (Quan trọng: Lưu Old Value vs New Value)
    # Lưu dưới dạng JSON: {"old": {price: 10}, "new": {price: 20}}
    changes = Column(JSON, nullable=True)
    
    # 6. Mô tả ngắn gọn (Human readable)
    description = Column(String(500), nullable=True)
    
    # 7. Thời gian & IP (Optional)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    ip_address = Column(String(50), nullable=True)

    # Relationships
    user = relationship("User", back_populates="logs")