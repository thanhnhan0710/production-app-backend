from sqlalchemy import Column, Integer, String
from app.db.base_class import Base

class Warehouse(Base):
    __tablename__ = "warehouses"

    warehouse_id = Column(Integer, primary_key=True, index=True)
    warehouse_name = Column(String(100), unique=True, nullable=False, index=True)
    location = Column(String(200), nullable=True)
    description = Column(String(255), nullable=True)