from typing import Optional
from sqlalchemy import Column, Integer, Float, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base

class InventoryStock(Base):
    __tablename__ = "inventory_stocks"

    id = Column(Integer, primary_key=True, index=True)
    
    # Tồn kho được định danh bởi bộ 3: Vật tư - Kho - Lô
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False)
    warehouse_id = Column(Integer, ForeignKey("warehouses.warehouse_id"), nullable=False)
    batch_id = Column(Integer, ForeignKey("batches.batch_id"), nullable=False)
    
    # Số lượng
    quantity_on_hand = Column(Float, default=0.0) # Tồn thực tế trong kho
    quantity_reserved = Column(Float, default=0.0) # Đã giữ chỗ cho đơn sản xuất (chưa xuất)
    
    # Tồn khả dụng = On Hand - Reserved
    # Cột này có thể tính toán, nhưng lưu DB để query cho nhanh nếu dữ liệu lớn

    last_updated = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Ràng buộc duy nhất: Một Lô hàng ở trong Một Kho chỉ có 1 dòng tồn kho
    __table_args__ = (
        UniqueConstraint('material_id', 'warehouse_id', 'batch_id', name='uix_stock_loc_batch'),
    )

    # Relationships
    material = relationship("Material")
    warehouse = relationship("Warehouse")
    batch = relationship("Batch")

     # --- [MỚI] PROPERTY MAPPING DỮ LIỆU TỪ BẢNG LIÊN QUAN ---
    
    @property
    def received_quantity_cones(self) -> int:
        """Lấy số cuộn từ Chi tiết phiếu nhập thông qua Batch"""
        if self.batch and self.batch.receipt_detail:
            return self.batch.receipt_detail.received_quantity_cones or 0
        return 0

    @property
    def number_of_pallets(self) -> int:
        """Lấy số pallet từ Chi tiết phiếu nhập thông qua Batch"""
        if self.batch and self.batch.receipt_detail:
            return self.batch.receipt_detail.number_of_pallets or 0
        return 0

    @property
    def supplier_short_name(self) -> Optional[str]:
        """
        Lấy tên NCC viết tắt.
        Chain: Inventory -> Batch -> ReceiptDetail -> ReceiptHeader -> PO -> Supplier
        """
        try:
            return self.batch.receipt_detail.header.po_header.vendor.short_name
        except AttributeError:
            # Fallback: Trả về tên đầy đủ nếu không có tên viết tắt, hoặc None nếu đứt gãy quan hệ
            try:
                return self.batch.receipt_detail.header.po_header.vendor.supplier_name
            except AttributeError:
                return None
