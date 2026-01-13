from sqlalchemy import Column, Integer, Date, String
from app.db.base_class import Base
from sqlalchemy.orm import relationship


class DyeColor(Base):
    __tablename__ = "dye_colors"

    color_id = Column(Integer, primary_key=True, index=True)
    color_name = Column(String(50), nullable=False)
    hex_code= Column(String(20), unique=True,nullable=True)
    note = Column(String(150), nullable=True)

    standards = relationship("Standard", back_populates="dye_color")
