from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base

class MachineProductHistory(Base):
    __tablename__ = "machine_product_histories"

    id = Column(Integer, primary_key=True, index=True)
    
    # Liên kết với Máy
    machine_id = Column(Integer, ForeignKey("machines.machine_id", ondelete="CASCADE"), nullable=False)
    
    # Liên kết với Sản phẩm
    product_id = Column(Integer, ForeignKey("products.product_id", ondelete="CASCADE"), nullable=False)
    
    # Thời gian bắt đầu chạy
    start_time = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Thời gian kết thúc (Nếu NULL nghĩa là đang chạy hiện tại)
    end_time = Column(DateTime(timezone=True), nullable=True)
    
    # Ghi chú thêm (Ví dụ: Chạy thử, Chạy đơn hàng VIP...)
    notes = Column(String(255), nullable=True)

    # Relationships
    machine = relationship("Machine", backref="product_histories")
    product = relationship("Product") # Giả định bạn đã có class Product