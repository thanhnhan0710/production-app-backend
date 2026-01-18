from sqlalchemy import Column, Integer, String, Float, DateTime, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base_class import Base
import datetime


class WeavingInspection(Base):
    __tablename__ = "weaving_inspections"

    id = Column(Integer, primary_key=True, index=True)
    
    # Liên kết về Phiếu rổ dệt
    weaving_basket_ticket_id = Column(Integer, ForeignKey("weaving_basket_tickets.id"), nullable=False)
    
    stage_name = Column(String(50), nullable=False) # Tên lần (Vào rổ, Lần 1, Lần 2...)
    
    # --- Các thông số đo đạc ---
    width_mm = Column(Float, nullable=True)         # Chiều rộng
    weft_density = Column(Float, nullable=True)     # Mật độ sợi ngang (pick/10cm)
    tension_dan = Column(Float, nullable=True)      # Lực căng (daN)
    thickness_mm = Column(Float, nullable=True)     # Độ dày
    weight_gm = Column(Float, nullable=True)        # Trọng lượng (g/m)
    bowing = Column(Float, nullable=True)           # Độ cong (Bowing/Skewing) - Thường tính bằng % hoặc mm
    
    # --- Thông tin người kiểm tra ---
    employee_id = Column(Integer, ForeignKey("employees.employee_id"), nullable=False)
    shift_id = Column(Integer, ForeignKey("shifts.shift_id"), nullable=False) # Mã ca
    inspection_time = Column(DateTime, default=datetime.datetime.now)

    # Relationships
    ticket = relationship("WeavingBasketTicket", back_populates="inspections")
    employee = relationship("Employee")
    shift = relationship("Shift")