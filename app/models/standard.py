from sqlalchemy import Column, Integer, String, ForeignKey, Text, Float
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class Standard(Base):
    __tablename__ = "standards"

    standard_id = Column(Integer, primary_key=True, index=True)
    
    # [QUAN TRỌNG] Thêm unique=True để đảm bảo 1 Product chỉ có 1 Standard
    product_id = Column(Integer, ForeignKey("products.product_id"), nullable=False, unique=True) 
    
    dye_color_id = Column(Integer, ForeignKey("dye_colors.color_id"), nullable=True)

    # Thông số vật lý
    width_mm = Column(String(50), nullable=False)                           
    thickness_mm = Column(String(50), nullable=False)                       
    breaking_strength_dan = Column(String(50), nullable=False)              
    elongation_at_load_percent = Column(String(50), nullable=False)       
    
    # Thông số màu & Hóa học (Nếu có nhuộm)
    color_fastness_dry = Column(String(50), nullable=True)                  
    color_fastness_wet = Column(String(50), nullable=True)                  
    delta_e = Column(String(50), nullable=True)                             

    # Thông số dệt & Ngoại quan
    appearance = Column(Text, nullable=True)                              
    weft_density = Column(String(50), nullable=False)                     
    weight_gm = Column(String(50), nullable=False)                          
    
    note = Column(Text, nullable=True)                                     

    # Quan hệ
    # Lưu ý: Bên model Product, relationship nên để uselist=False 
    # Ví dụ: standard = relationship("Standard", back_populates="product", uselist=False)
    product = relationship("Product", back_populates="standards") 
    dye_color = relationship("DyeColor", back_populates="standards")