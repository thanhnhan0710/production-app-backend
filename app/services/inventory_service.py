from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_, desc
from fastapi import HTTPException
from typing import List, Dict, Any

from app.models.inventory import InventoryStock
from app.models.material import Material
from app.models.batch import Batch
# Import các model liên quan để join
from app.models.material_receipt import MaterialReceiptDetail, MaterialReceipt
from app.models.purchase_order import PurchaseOrderHeader
from app.models.supplier import Supplier

from app.schemas.inventory_schema import InventoryAdjustment

class InventoryService:
    def __init__(self, db: Session):
        self.db = db

    # --- [MỚI] LẤY DANH SÁCH TỒN KHO (Phân trang & Tìm kiếm) ---
    def get_multi(
        self, 
        skip: int = 0, 
        limit: int = 100, 
        search: str = None, 
        warehouse_id: int = None
    ) -> List[InventoryStock]:
        """
        Lấy danh sách tồn kho.
        """
        query = self.db.query(InventoryStock)

        # [TỐI ƯU] Eager Load các relationship sâu để lấy dữ liệu cho Property
        # Inventory -> Batch -> ReceiptDetail -> Header -> PO -> Supplier
        query = query.options(
            joinedload(InventoryStock.material),
            joinedload(InventoryStock.warehouse),
            joinedload(InventoryStock.batch)
                .joinedload(Batch.receipt_detail)
                .joinedload(MaterialReceiptDetail.header)
                .joinedload(MaterialReceipt.po_header)
                .joinedload(PurchaseOrderHeader.vendor)
        )

        # Filter Warehouse
        if warehouse_id:
            query = query.filter(InventoryStock.warehouse_id == warehouse_id)

        # Search Logic
        if search:
            search_term = f"%{search}%"
            # Cần join rõ ràng để filter (dù đã options joinedload ở trên dùng để select)
            query = query.join(InventoryStock.material).join(InventoryStock.batch)
            
            query = query.filter(
                or_(
                    Material.material_code.ilike(search_term),
                    Batch.supplier_batch_no.ilike(search_term),
                    Batch.internal_batch_code.ilike(search_term)
                )
            )
        
        return query.order_by(desc(InventoryStock.last_updated)).offset(skip).limit(limit).all()

    def get_stock_by_batch(self, warehouse_id: int, batch_id: int) -> InventoryStock:
        return self.db.query(InventoryStock).filter(
            InventoryStock.warehouse_id == warehouse_id,
            InventoryStock.batch_id == batch_id
        ).options(
            joinedload(InventoryStock.material),
            joinedload(InventoryStock.batch)
        ).first()

    def get_total_stock_by_material(self, material_id: int) -> Dict[str, Any]:
        """Tính tổng tồn kho của 1 loại sợi ở tất cả các kho và các lô"""
        result = self.db.query(
            func.sum(InventoryStock.quantity_on_hand).label("total_on_hand"),
            func.sum(InventoryStock.quantity_reserved).label("total_reserved")
        ).filter(InventoryStock.material_id == material_id).first()
        
        if not result:
            return {
                "material_id": material_id,
                "total_on_hand": 0.0,
                "total_reserved": 0.0,
                "total_available": 0.0
            }

        on_hand = result.total_on_hand if result.total_on_hand is not None else 0.0
        reserved = result.total_reserved if result.total_reserved is not None else 0.0
        
        return {
            "material_id": material_id,
            "total_on_hand": on_hand,
            "total_reserved": reserved,
            "total_available": on_hand - reserved
        }

    def increase_stock(self, material_id: int, warehouse_id: int, batch_id: int, quantity: float, commit: bool = True):
        """
        Tăng/Giảm tồn kho.
        param commit: Nếu True thì commit ngay (dùng cho API lẻ). Nếu False thì chỉ flush (dùng cho Transaction lớn).
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
        
        current_qty = stock.quantity_on_hand or 0.0
        stock.quantity_on_hand = current_qty + quantity
        
        if commit:
            self.db.commit()
            self.db.refresh(stock)
        else:
            self.db.flush() # Chỉ đẩy xuống DB để check constraint, chưa chốt
            
        return stock

    def reserve_stock(self, material_id: int, quantity_needed: float):
        stocks = self.db.query(InventoryStock).filter(
            InventoryStock.material_id == material_id,
            InventoryStock.quantity_on_hand > InventoryStock.quantity_reserved
        ).order_by(InventoryStock.batch_id.asc()).all()

        remaining_need = quantity_needed
        reserved_logs = []

        for stock in stocks:
            if remaining_need <= 0:
                break
            
            on_hand = stock.quantity_on_hand or 0.0
            reserved = stock.quantity_reserved or 0.0
            available = on_hand - reserved
            
            if available <= 0:
                continue

            take = min(available, remaining_need)
            
            stock.quantity_reserved = reserved + take
            remaining_need -= take
            
            reserved_logs.append({
                "batch_id": stock.batch_id,
                "reserved_qty": take
            })
            self.db.add(stock)

        if remaining_need > 0.001:
            self.db.rollback() 
            raise HTTPException(status_code=400, detail=f"Không đủ tồn kho khả dụng để giữ chỗ. Thiếu {remaining_need}")
        
        self.db.commit()
        return reserved_logs

    def adjust_stock(self, adjustment: InventoryAdjustment):
        stock = self.get_stock_by_batch(adjustment.warehouse_id, adjustment.batch_id)
        if not stock:
            if adjustment.new_quantity > 0:
                stock = self.increase_stock(
                    material_id=adjustment.material_id, 
                    warehouse_id=adjustment.warehouse_id, 
                    batch_id=adjustment.batch_id, 
                    quantity=adjustment.new_quantity
                )
            else:
                raise HTTPException(status_code=404, detail="Không tìm thấy dữ liệu tồn kho để điều chỉnh.")
        else:
            stock.quantity_on_hand = adjustment.new_quantity
            self.db.add(stock)
            self.db.commit()
            self.db.refresh(stock)
        
        return stock