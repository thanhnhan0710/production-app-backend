from sqlalchemy import Column, Integer, String
from app.db.base import Base
from sqlalchemy.orm import relationship

class Product(Base):
    __tablename__ = "products"

    product_id = Column(Integer, primary_key=True, index=True)
    item_code = Column(String(100), unique=True, nullable=False)
    note = Column(String(255), nullable=True)
    standards = relationship("Standard", back_populates="product")