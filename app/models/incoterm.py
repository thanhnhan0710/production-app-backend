from sqlalchemy import Column, Integer, String
from app.db.base_class import Base

class Incoterm(Base):
    __tablename__ = "incoterms"

    incoterm_id = Column(Integer, primary_key=True, index=True)
    
    # Mã điều kiện (VD: EXW, FOB, CIF, DDP, DAP)
    incoterm_code = Column(String(10), unique=True, index=True, nullable=False)
    
    # Mô tả chi tiết (VD: Giao tại xưởng, Giao lên tàu...)
    description = Column(String(255), nullable=True)

    def __repr__(self):
        return f"<Incoterm {self.incoterm_code}>"