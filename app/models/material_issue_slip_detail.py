from sqlalchemy import Column, Integer, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from app.db.base import Base


class MaterialIssueSlipDetail(Base):
    __tablename__ = "material_issue_slip_details"

    issue_detail_id = Column(Integer, primary_key=True, index=True)

    issue_slip_id = Column(
        Integer,
        ForeignKey("material_issue_slips.issue_slip_id", ondelete="CASCADE"),
        nullable=False
    )

    material_id = Column(
        Integer,
        ForeignKey("materials.material_id"),
        nullable=False
    )

    quantity = Column(Numeric(12, 2), nullable=False)

    unit_id = Column(
        Integer,
        ForeignKey("units.unit_id"),
        nullable=False
    )

    shift_id = Column(
        Integer,
        ForeignKey("shifts.shift_id"),
        nullable=False
    )

    employee_id = Column(
        Integer,
        ForeignKey("employees.employee_id"),
        nullable=False
    )


    issue_slip = relationship("MaterialIssueSlip", lazy="joined")
    material = relationship("Material", lazy="joined")
    unit = relationship("Unit", lazy="joined")
    shift = relationship("Shift", lazy="joined")
    employee = relationship("Employee", lazy="joined")
