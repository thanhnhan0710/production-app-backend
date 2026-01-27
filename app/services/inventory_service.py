from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException
from typing import List
from app.models.inventory import InventoryStock
from app.schemas.inventory_schema import InventoryAdjustment

class InventoryService:
    def __init__(self, db: Session):
        self.db = db

    def get_stock_by_batch(self, warehouse_id: int, batch_id: int) -> InventoryStock:
        return self.db.query(InventoryStock).filter(
            InventoryStock.warehouse_id == warehouse_id,
            InventoryStock.batch_id == batch_id
        ).first()

    def get_total_stock_by_material(self, material_id: int):
        """Tính tổng tồn kho của 1 loại sợi ở tất cả các kho và các lô"""
        result = self.db.query(
            func.sum(InventoryStock.quantity_on_hand).label("total_on_hand"),
            func.sum(InventoryStock.quantity_reserved).label("total_reserved")
        ).filter(InventoryStock.material_id == material_id).first()
        
        return {
            "material_id": material_id,
            "total_on_hand": result.total_on_hand or 0.0,
            "total_reserved": result.total_reserved or 0.0,
            "total_available": (result.total_on_hand or 0.0) - (result.total_reserved or 0.0)
        }

    def increase_stock(self, material_id: int, warehouse_id: int, batch_id: int, quantity: float):
        """
        Hàm dùng khi Nhập kho (Goods Receipt).
        Tự động tạo dòng mới nếu chưa có hoặc cộng dồn nếu đã có.
        """
        stock = self.db.query(InventoryStock).filter(
            InventoryStock.material_id == material_id,
            InventoryStock.warehouse_id == warehouse_id,
            InventoryStock.batch_id == batch_id
        ).first()

        if not stock:
            stock = InventoryStock(
                material_id=material_id,
                warehouse_id=warehouse_id,
                batch_id=batch_id,
                quantity_on_hand=0.0,
                quantity_reserved=0.0
            )
            self.db.add(stock)
        
        stock.quantity_on_hand += quantity
        self.db.commit()
        self.db.refresh(stock)
        return stock

    def reserve_stock(self, material_id: int, quantity_needed: float):
        """
        Hàm dùng cho Kế hoạch sản xuất.
        Logic FEFO (First Expire First Out) hoặc FIFO (First In First Out).
        Tự động giữ chỗ trên các lô cũ nhất.
        """
        # Lấy danh sách các lô có tồn > 0, sắp xếp theo ngày nhập (batch_id tăng dần hoặc created_at)
        # TODO: Cần join với bảng Batch để check qc_status == PASS mới được reserve
        stocks = self.db.query(InventoryStock).filter(
            InventoryStock.material_id == material_id,
            InventoryStock.quantity_on_hand > InventoryStock.quantity_reserved
        ).order_by(InventoryStock.batch_id.asc()).all()

        remaining_need = quantity_needed
        reserved_logs = []

        for stock in stocks:
            if remaining_need <= 0:
                break
            
            available = stock.quantity_on_hand - stock.quantity_reserved
            if available <= 0:
                continue

            take = min(available, remaining_need)
            
            stock.quantity_reserved += take
            remaining_need -= take
            
            reserved_logs.append({
                "batch_id": stock.batch_id,
                "reserved_qty": take
            })
            self.db.add(stock)

        if remaining_need > 0:
            # Không đủ hàng để giữ chỗ
            self.db.rollback() # Hoàn tác
            raise HTTPException(status_code=400, detail=f"Không đủ tồn kho khả dụng để giữ chỗ. Thiếu {remaining_need}")
        
        self.db.commit()
        return reserved_logs

    def adjust_stock(self, adjustment: InventoryAdjustment):
        """Dùng cho kiểm kê kho (Stock Take)"""
        stock = self.get_stock_by_batch(adjustment.warehouse_id, adjustment.batch_id)
        if not stock:
            # Nếu chưa có dòng tồn kho mà muốn điều chỉnh dương -> Tạo mới
            if adjustment.new_quantity > 0:
                stock = self.increase_stock(
                    adjustment.material_id, 
                    adjustment.warehouse_id, 
                    adjustment.batch_id, 
                    adjustment.new_quantity
                )
            else:
                raise HTTPException(status_code=404, detail="Không tìm thấy dữ liệu tồn kho để điều chỉnh.")
        else:
            stock.quantity_on_hand = adjustment.new_quantity
            self.db.add(stock)
            self.db.commit()
            self.db.refresh(stock)
        
        return stock