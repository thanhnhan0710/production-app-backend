from sqlalchemy import Column, Integer, Date, String
from app.db.base_class import Base


class MaterialIssueSlip(Base):
    __tablename__ = "material_issue_slips"

    issue_slip_id = Column(Integer, primary_key=True, index=True)
    issue_date = Column(Date, nullable=False)
    note = Column(String(255), nullable=True)
