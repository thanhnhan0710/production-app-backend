from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class Unit(Base):
    __tablename__ = "units"

    unit_id = Column(Integer, primary_key=True, index=True)
    unit_name = Column(String(50), nullable=False, unique=True)
    note= Column(String(150), nullable=True)

