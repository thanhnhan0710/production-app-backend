from sqlalchemy import Column, Integer, String, Float, DateTime, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base_class import Base
import datetime

# 1. Bảng Phiếu thông tin rổ dệt
class WeavingBasketTicket(Base):
    __tablename__ = "weaving_basket_tickets"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True)

    # --- Thông tin sản xuất ---
    product_id = Column(Integer, ForeignKey("products.product_id"), nullable=False)
    standard_id = Column(Integer, ForeignKey("standards.standard_id"), nullable=False)
    machine_id = Column(Integer, ForeignKey("machines.machine_id"), nullable=False)
    
    # Lưu ý: Cột này bạn mới thêm ở bước trước, hãy giữ lại
    machine_line = Column(Integer, nullable=True)
    
    # --- Thông tin sợi & Rổ ---
    yarn_load_date = Column(Date, nullable=False)        # Ngày lên sợi
    
    # [CHANGE] Thay yarn_lot_id bằng batch_id
    # Liên kết tới bảng 'batches' thông qua cột khóa chính 'batch_id'
    batch_id = Column(Integer, ForeignKey("batches.batch_id"), nullable=True) 
    
    basket_id = Column(Integer, ForeignKey("baskets.basket_id"), nullable=False)  
    
    # --- Quy trình Vào rổ (Start) ---
    time_in = Column(DateTime, default=datetime.datetime.now) 
    employee_in_id = Column(Integer, ForeignKey("employees.employee_id"), nullable=False) 
    
    # --- Quy trình Ra rổ (Finish) ---
    time_out = Column(DateTime, nullable=True)           # Thời gian ra rổ
    employee_out_id = Column(Integer, ForeignKey("employees.employee_id"), nullable=True) # NV ra
    
    # --- Thông số kết quả ---
    gross_weight = Column(Float, nullable=True)          # Tổng trọng lượng (Cả bì)
    net_weight = Column(Float, nullable=True)            # Trọng lượng tịnh (Trừ bì)
    length_meters = Column(Float, nullable=True)         # Chiều dài (m)
    number_of_knots = Column(Integer, default=0)         # Số mối nối

    # --- Relationships ---
    employee_in = relationship("Employee", foreign_keys=[employee_in_id])
    employee_out = relationship("Employee", foreign_keys=[employee_out_id])
    
    basket = relationship("Basket")
    product = relationship("Product")
    inspections = relationship("WeavingInspection", back_populates="ticket")
    
    # [NEW] Relationship để truy cập thông tin Batch từ Ticket
    batch = relationship("Batch")