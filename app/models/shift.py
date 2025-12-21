from sqlalchemy import Column, Integer, String
from app.db.base import Base

class Shift(Base):
    __tablename__ = "shifts"

    shift_id = Column(Integer, primary_key=True, index=True)
    shift_name = Column(String(50), nullable=False)
    note = Column(String(255), nullable=True)
