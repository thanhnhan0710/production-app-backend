from sqlalchemy import Column, Integer, ForeignKey,String
from sqlalchemy.orm import relationship
from app.db.base import Base

class YarnIssueSlipDetail(Base):
    __tablename__ = "yarn_issue_slip_details"

    issue_detail_id = Column(Integer, primary_key=True, index=True)

    issue_slip_id = Column(Integer, ForeignKey("yarn_issue_slips.issue_slip_id"), nullable=False)

    lot_code = Column(String(50), nullable=False)
    yarn_id = Column(Integer, nullable=False)

    machine_id = Column(Integer, ForeignKey("machines.machine_id"))
    product_id = Column(Integer, ForeignKey("products.product_id"))

    quantity = Column(Integer, nullable=False)
    unit_id = Column(Integer, ForeignKey("units.unit_id"))

    shift_id = Column(Integer, ForeignKey("shifts.shift_id"))
    employee_id = Column(Integer, ForeignKey("employees.employee_id"))

    # 🔗 Relationships
    issue_slip = relationship("YarnIssueSlip", back_populates="details")
    machine = relationship("Machine")
    product = relationship("Product")
    unit = relationship("Unit")
    shift = relationship("Shift")
    employee = relationship("Employee")
