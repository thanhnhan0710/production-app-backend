from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class MaterialReceiptDetail(Base):
    __tablename__ = "material_receipt_details"

    detail_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    receipt_id = Column(Integer, ForeignKey("material_receipts.receipt_id"), nullable=False)
    material_id = Column(Integer, ForeignKey("materials.material_id"), nullable=False)
    
    # Số lượng PO (Tham khảo)
    po_quantity_kg = Column(Float, default=0.0, comment="SL Kg trên chứng từ")
    po_quantity_cones = Column(Integer, default=0, comment="SL Cuộn trên chứng từ")
    
    # Số lượng thực nhận
    received_quantity_kg = Column(Float, nullable=False, comment="SL Kg thực nhập")
    received_quantity_cones = Column(Integer, default=0, comment="SL Cuộn thực nhập")
    
    # Đóng gói
    number_of_pallets = Column(Integer, default=0, comment="Tổng số Pallet/Kiện hàng")

    supplier_batch_no = Column(String(100), nullable=True)
    origin_country = Column(String(50), nullable=True)

    # Vị trí đặt hàng trong kho
    location = Column(String(20), nullable=True, comment="Vị trí kho chi tiết (Bin Code)")

    note = Column(String(200), nullable=True)

    # Relationships
    header = relationship("MaterialReceipt", back_populates="details")
    material = relationship("Material")