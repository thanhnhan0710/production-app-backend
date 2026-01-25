import enum
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class BOMComponentType(str, enum.Enum):
    GROUND = "Ground"
    GRD_MARKER = "Grd. Marker"
    EDGE = "Edge"
    BINDER = "Binder"
    STUFFER = "Stuffer"
    CATCH_CORD = "Catch cord"
    FILLING = "Filling"
    SECOND_FILLING = "2nd Filling"

class BOMDetail(Base):
    __tablename__ = "bom_details"

    detail_id = Column(Integer, primary_key=True, index=True)
    bom_id = Column(Integer, ForeignKey("bom_headers.bom_id"), nullable=False)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False)
    
    # Loại thành phần (Cột A trong Excel)
    component_type = Column(Enum(BOMComponentType), nullable=False)
    
    # --- CÁC TRƯỜNG KỸ THUẬT CHI TIẾT ---
    
    threads = Column(Integer, default=0, comment="Số đầu sợi (Cột B)")
    yarn_dtex = Column(Float, comment="Độ mảnh sợi dtex (Cột C)")
    yarn_type_name = Column(String(100), comment="Mã sợi/Màu (Cột D - VD: 03300-PES-WEISS)")
    
    twisted = Column(Float, default=1.0, comment="Hệ số xoắn (Cột E)")
    crossweave_rate = Column(Float, default=0.0, comment="Độ dôi sợi/Crimp % (Cột F)")
    
    # Kết quả tính toán
    weight_per_yarn_gm = Column(Float, comment="Trọng lượng lý thuyết g/m (Cột G)")
    
    # Thông số đo đạc thực tế (Lab test)
    actual_length_cm = Column(Float, comment="Chiều dài sợi thực tế đo được (Cột H)")
    actual_weight_cal = Column(Float, comment="Trọng lượng thực tế tính toán (Cột I)")
    
    weight_percentage = Column(Float, comment="Tỷ lệ % khối lượng (Cột J)")
    bom_gm = Column(Float, comment="Định mức chốt cuối cùng (Cột K)")

    note = Column(String(200), nullable=True)

    header = relationship("BOMHeader", back_populates="bom_details")
    material = relationship("Material")