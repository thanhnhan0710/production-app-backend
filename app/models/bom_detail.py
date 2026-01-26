import enum
# 1. Thêm import DECIMAL
from sqlalchemy import Column, Integer, String, ForeignKey, Enum, DECIMAL
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class BOMComponentType(str, enum.Enum):
    GROUND = "GROUND"
    GRD_MARKER = "GRD. MARKER"
    EDGE = "EDGE"
    BINDER = "BINDER"
    STUFFER = "STUFFER"
    STUFFER_MAKER= "STUFFER MAKER"
    LOCK= "LOCK"
    CATCH_CORD = "CATCH CORD"
    FILLING = "FILLING"
    SECOND_FILLING = "2ND FILLING"

class BOMDetail(Base):
    __tablename__ = "bom_details"

    detail_id = Column(Integer, primary_key=True, index=True)
    bom_id = Column(Integer, ForeignKey("bom_headers.bom_id"), nullable=False)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False)
    
    component_type = Column(
        Enum(
            BOMComponentType, 
            create_constraint=False,
            values_callable=lambda obj: [e.value for e in obj] 
        ), 
        nullable=False
    )
    
    # Giữ nguyên Integer vì số sợi là số nguyên
    threads = Column(Integer, default=0, comment="Số đầu sợi (Cột B)")

    # --- CÁC CỘT ĐÃ CHUYỂN SANG DECIMAL(20, 10) ---

    yarn_dtex = Column(DECIMAL(20, 10), comment="Độ mảnh sợi dtex (Cột C)")
    
    yarn_type_name = Column(String(100), comment="Mã sợi/Màu (Cột D)")
    
    # Default cũng nên để string hoặc decimal để tránh ép kiểu ngầm định ban đầu
    twisted = Column(DECIMAL(20, 10), default=1.0, comment="Hệ số xoắn (Cột E)")
    
    crossweave_rate = Column(DECIMAL(20, 10), default=0.0, comment="Độ dôi sợi/Crimp % (Cột F)")
    
    weight_per_yarn_gm = Column(DECIMAL(20, 10), comment="Trọng lượng lý thuyết g/m (Cột G)")
    
    actual_length_cm = Column(DECIMAL(20, 10), comment="Chiều dài sợi thực tế đo được (Cột H)")
    
    actual_weight_cal = Column(DECIMAL(20, 10), comment="Trọng lượng thực tế tính toán (Cột I)")
    
    weight_percentage = Column(DECIMAL(20, 10), comment="Tỷ lệ % khối lượng (Cột J)")
    
    bom_gm = Column(DECIMAL(20, 10), comment="Định mức chốt cuối cùng (Cột K)")
    
    # ---------------------------------------------

    note = Column(String(200), nullable=True)

    header = relationship("BOMHeader", back_populates="bom_details")
    material = relationship("Material")