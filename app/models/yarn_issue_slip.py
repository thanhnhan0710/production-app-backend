from sqlalchemy import Column, Integer, String, Date
from sqlalchemy.orm import relationship
from app.db.base import Base

class YarnIssueSlip(Base):
    __tablename__ = "yarn_issue_slips"

    issue_slip_id = Column(Integer, primary_key=True, index=True)
    issue_date = Column(Date, nullable=False)
    note = Column(String(255), nullable=True)

    # 1 phiếu xuất có nhiều chi tiết
    details = relationship(
        "YarnIssueSlipDetail",
        back_populates="issue_slip",
        cascade="all, delete-orphan"
    )
