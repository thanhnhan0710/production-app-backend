from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class Machine(Base):
    __tablename__ = "machines"

    machine_id = Column(Integer, primary_key=True, index=True)
    machine_name = Column(String(100), nullable=False)

    total_lines = Column(Integer, nullable=True)
    purpose = Column(String(255), nullable=True)

    status = Column(
        String(20),
        nullable=False,
        default="stopped"  # running / stopped / mainternance
    )
