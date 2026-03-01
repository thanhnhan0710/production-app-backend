from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base

class WeavingProduction(Base):
    __tablename__ = "weaving_productions"

    id = Column(Integer, primary_key=True, index=True)

    # --- LIÊN KẾT MÁY DỆT (WEAVING MACHINE) ---
    # [CẬP NHẬT] Đổi ForeignKey trỏ thẳng vào bảng weaving_machines thay vì machines
    # Điều này đảm bảo tính toàn vẹn: Chỉ máy dệt mới có sản lượng dệt.
    machine_id = Column(Integer, ForeignKey("weaving_machines.machine_id"), nullable=False)
    
    # Line vẫn giữ nguyên (vì 1 máy dệt có thể có nhiều line 1, 2...)
    line = Column(Integer, nullable=False) 

    # --- LIÊN KẾT RỔ (BASKET) ---
    basket_id = Column(Integer, ForeignKey("baskets.basket_id"), nullable=False)

    # --- LIÊN KẾT CA (SHIFT) ---
    shift_id = Column(Integer, ForeignKey("shifts.shift_id"), nullable=True)

    # --- SỐ LIỆU SẢN XUẤT ---
    total_weight = Column(Float, default=0.0, nullable=False)
    run_waste = Column(Float, default=0.0, nullable=False)
    setup_waste = Column(Float, default=0.0, nullable=False)

    # --- THÔNG TIN AUDIT ---
    updated_by_id = Column(Integer, ForeignKey("employees.employee_id"), nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # ==========================================
    # QUAN HỆ (RELATIONSHIPS)
    # ==========================================
    
    # 1. Quan hệ với Máy Dệt (Trỏ tới Class WeavingMachine thay vì Machine)
    machine = relationship("WeavingMachine", back_populates="weaving_productions")

    # 2. Quan hệ với Rổ
    basket = relationship("Basket", back_populates="weaving_productions")

    # 3. Quan hệ với Ca
    shift = relationship("Shift", back_populates="weaving_productions")

    # 4. Quan hệ với Nhân viên (Người cập nhật)
    updated_by = relationship("Employee", back_populates="weaving_updates")