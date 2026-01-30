from sqlalchemy import Column, Integer, String, Float, DateTime, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base_class import Base
import datetime

# =======================================================
# 1. Bảng Chi tiết các lô sợi trong phiếu (New Table)
# =======================================================
class WeavingTicketYarn(Base):
    """
    Bảng này lưu trữ thông tin: Phiếu này dùng Batch nào cho thành phần nào?
    Ví dụ: 
    - Ticket A dùng Batch #101 cho 'GROUND', số lượng 50kg
    - Ticket A dùng Batch #205 cho 'FILLING', số lượng 30kg
    """
    __tablename__ = "weaving_ticket_yarns"

    id = Column(Integer, primary_key=True, index=True)
    
    # Liên kết với Phiếu rổ dệt
    ticket_id = Column(Integer, ForeignKey("weaving_basket_tickets.id"), nullable=False)
    
    # Liên kết với Lô sợi (Batch)
    batch_id = Column(Integer, ForeignKey("batches.batch_id"), nullable=False)
    
    # Loại thành phần (Lấy từ Enum BOMComponentType: GROUND, FILLING, BINDER...)
    component_type = Column(String(50), nullable=False) 
    
    # [MỚI] Số lượng xuất (kg)
    quantity = Column(Float, default=0.0) 
    
    # Ghi chú thêm (nếu cần)
    note = Column(String(255), nullable=True)

    # --- Relationships ---
    batch = relationship("Batch")
    ticket = relationship("WeavingBasketTicket", back_populates="yarns")


# =======================================================
# 2. Bảng Phiếu thông tin rổ dệt (Updated Table)
# =======================================================
class WeavingBasketTicket(Base):
    __tablename__ = "weaving_basket_tickets"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True)

    # --- Thông tin sản xuất ---
    product_id = Column(Integer, ForeignKey("products.product_id"), nullable=False)
    standard_id = Column(Integer, ForeignKey("standards.standard_id"), nullable=True)
    machine_id = Column(Integer, ForeignKey("machines.machine_id"), nullable=False)
    machine_line = Column(Integer, nullable=False)
    
    # --- Thông tin Rổ ---
    yarn_load_date = Column(Date, nullable=False)
    basket_id = Column(Integer, ForeignKey("baskets.basket_id"), nullable=True)  
    
    # --- Quy trình Vào rổ (Start) ---
    time_in = Column(DateTime, default=datetime.datetime.now) 
    employee_in_id = Column(Integer, ForeignKey("employees.employee_id"), nullable=True)
    
    # --- Quy trình Ra rổ (Finish) ---
    time_out = Column(DateTime, nullable=True)
    employee_out_id = Column(Integer, ForeignKey("employees.employee_id"), nullable=True)
    
    # --- Thông số kết quả ---
    gross_weight = Column(Float, nullable=True)
    net_weight = Column(Float, nullable=True)
    length_meters = Column(Float, nullable=True)
    number_of_knots = Column(Integer, default=0)

    # --- Relationships ---
    employee_in = relationship("Employee", foreign_keys=[employee_in_id])
    employee_out = relationship("Employee", foreign_keys=[employee_out_id])
    
    basket = relationship("Basket")
    product = relationship("Product")
    inspections = relationship("WeavingInspection", back_populates="ticket")
    
    # Relationship 1-N: Một phiếu có nhiều lô sợi thành phần
    yarns = relationship("WeavingTicketYarn", back_populates="ticket", cascade="all, delete-orphan")