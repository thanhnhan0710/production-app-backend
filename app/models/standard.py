from sqlalchemy import Column, Integer, String, ForeignKey, Text, Float
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class Standard(Base):
    __tablename__ = "standards"

    standard_id = Column(Integer, primary_key=True, index=True)
    
    # [QUAN TRỌNG] Thêm unique=True để đảm bảo 1 Product chỉ có 1 Standard
    product_id = Column(Integer, ForeignKey("products.product_id"), nullable=False, unique=True) 

    # Thông số vật lý
    width_mm = Column(String(50), nullable=False)                           
    thickness_mm = Column(String(50), nullable=False)                       
    breaking_strength_dan = Column(String(50), nullable=False)              
    elongation_at_load_percent = Column(String(50), nullable=False)         
    curved = Column(String(50), nullable=True) # [MỚI] Thêm trường curved (Độ cong)                            

    # Thông số dệt & Ngoại quan                        
    weft_density = Column(String(50), nullable=False)                     
    weight_gm = Column(String(50), nullable=False)
    
    note = Column(Text, nullable=True)                                      
    
    # Quan hệ 1-1 với Product
    product = relationship("Product", back_populates="standards")