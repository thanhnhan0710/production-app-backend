# app/models/weaving_production.py

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base


class WeavingProduction(Base):
    __tablename__ = "weaving_productions"

    id = Column(Integer, primary_key=True, index=True)

    # --- LIÊN KẾT MÁY DỆT ---
    machine_id = Column(
        Integer, ForeignKey("weaving_machines.machine_id"), nullable=False
    )
    line = Column(Integer, nullable=False)

    # --- LIÊN KẾT RỔ ---
    basket_id = Column(Integer, ForeignKey("baskets.basket_id"), nullable=False)

    # --- [MỚI] LIÊN KẾT PHIẾU RỔ DỆT (để biết sản lượng thuộc mã SP nào) ---
    weaving_ticket_id = Column(
        Integer,
        ForeignKey("weaving_basket_tickets.id"),
        nullable=True,
        index=True,
    )

    # --- LIÊN KẾT CA ---
    shift_id = Column(Integer, ForeignKey("shifts.shift_id"), nullable=True)

    # --- SỐ LIỆU SẢN XUẤT ---
    total_weight = Column(Float, default=0.0, nullable=False)
    run_waste = Column(Float, default=0.0, nullable=False)
    run_waste_reason = Column(String(255), nullable=True)   # [MỚI] Lý do phế run
    setup_waste = Column(Float, default=0.0, nullable=False)

    # --- THÔNG TIN AUDIT ---
    updated_by_id = Column(
        Integer, ForeignKey("employees.employee_id"), nullable=True
    )
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # ==========================================
    # QUAN HỆ (RELATIONSHIPS)
    # ==========================================
    machine = relationship("WeavingMachine", back_populates="weaving_productions")
    basket = relationship("Basket", back_populates="weaving_productions")
    shift = relationship("Shift", back_populates="weaving_productions")
    updated_by = relationship("Employee", back_populates="weaving_updates")

    # [MỚI] Quan hệ với Phiếu rổ dệt (để join lấy mã SP)
    weaving_ticket = relationship(
        "WeavingBasketTicket", back_populates="weaving_productions"
    )