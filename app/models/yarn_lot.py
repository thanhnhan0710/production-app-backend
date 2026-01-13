from sqlalchemy import Column, Integer, String, Date, ForeignKey, Float
from sqlalchemy.orm import relationship
from app.db.base_class import Base


class YarnLot(Base):
    __tablename__ = "yarn_lots"

    id = Column(Integer, primary_key=True, index=True)
   
    lot_code = Column(String(50), unique=True, index=True)
    yarn_id = Column(Integer, ForeignKey("yarns.yarn_id"),nullable=False)

    # Thông tin nhập
    import_date = Column(Date, nullable=False)

    # Thông tin số lượng
    total_kg = Column(Float, nullable=False)          # số kg
    roll_count = Column(Integer, nullable=False)      # số cuộn

    #  Vị trí & vận chuyển
    warehouse_location = Column(String(100), nullable=True)  # vị trí kho
    container_code = Column(String(50), nullable=True)       # mã container

    #  Nhân sự liên quan
    driver_id = Column(Integer, ForeignKey("employees.employee_id"), nullable=True)
    receiver_id = Column(Integer, ForeignKey("employees.employee_id"), nullable=False)
    updated_by = Column(Integer, ForeignKey("employees.employee_id"), nullable=False)

    note= Column(String(150), nullable=True)

    #  Relationships
    yarn = relationship("Yarn", back_populates="yarn_lots")

    driver = relationship(
        "Employee",
        foreign_keys=[driver_id],
        lazy="joined"
    )

    receiver = relationship(
        "Employee",
        foreign_keys=[receiver_id],
        lazy="joined"
    )

    updater = relationship(
        "Employee",
        foreign_keys=[updated_by],
        lazy="joined"
    )
