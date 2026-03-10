from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
import io
import openpyxl
from datetime import datetime

from app.models.material_inventory import MaterialInventory
from app.models.material_batch import MaterialBatch
from app.models.material_receipt_detail import MaterialReceiptDetail
from app.models.material_receipt import MaterialReceipt
from app.models.material import Material
from app.schemas.material_inventory_schema import MaterialInventoryCreate, MaterialInventoryUpdate, InventoryInitStock

# [SỬA LỖI 500 Ở ĐÂY]: Bắt buộc phải import material_batch_service để sinh mã lô tự động
from app.services.material_batch_service import material_batch_service

class MaterialInventoryService:
    def count_inventories(self, db: Session) -> int:
        return db.query(MaterialInventory).count()

    def get_inventory(self, db: Session, inventory_id: int) -> Optional[MaterialInventory]:
        return db.query(MaterialInventory).filter(MaterialInventory.inventory_id == inventory_id).first()

    def get_inventories(
        self, db: Session, warehouse_id: Optional[int] = None, material_id: Optional[int] = None, 
        is_low_stock: bool = False, skip: int = 0, limit: int = 100
    ) -> List[MaterialInventory]:
        
        query = db.query(MaterialInventory).options(
            joinedload(MaterialInventory.warehouse),
            joinedload(MaterialInventory.material),
            joinedload(MaterialInventory.batch)
                .joinedload(MaterialBatch.receipt_detail)
                .joinedload(MaterialReceiptDetail.header)
        )
        
        if warehouse_id: query = query.filter(MaterialInventory.warehouse_id == warehouse_id)
        if material_id: query = query.filter(MaterialInventory.material_id == material_id)
        
        # Filter sắp hết hàng
        if is_low_stock:
            query = query.join(MaterialInventory.material).filter(MaterialInventory.quantity_kg < Material.min_stock_level)
            
        results = query.order_by(MaterialInventory.updated_at.desc()).offset(skip).limit(limit).all()
        
        for inv in results:
            inv.warehouse_name = getattr(inv.warehouse, 'name', None) or getattr(inv.warehouse, 'warehouse_name', str(inv.warehouse_id))
            inv.material_code = inv.material.material_code if inv.material else str(inv.material_id)
            inv.batch_code = inv.batch.batch_code if inv.batch else str(inv.batch_id)
            
            inv.po_number = "N/A"
            if inv.batch and inv.batch.receipt_detail and inv.batch.receipt_detail.header and getattr(inv.batch.receipt_detail.header, 'po_header', None):
                inv.po_number = getattr(inv.batch.receipt_detail.header.po_header, 'po_number', "N/A")
                
        return results

    def export_excel(
        self, db: Session, warehouse_id: Optional[int] = None, material_id: Optional[int] = None,
        is_low_stock: bool = False
    ) -> io.BytesIO:
        
        query = db.query(MaterialInventory).options(
            joinedload(MaterialInventory.warehouse),
            joinedload(MaterialInventory.material),
            joinedload(MaterialInventory.batch)
                .joinedload(MaterialBatch.receipt_detail)
                .joinedload(MaterialReceiptDetail.header)
        )
        
        if warehouse_id: query = query.filter(MaterialInventory.warehouse_id == warehouse_id)
        if material_id: query = query.filter(MaterialInventory.material_id == material_id)
        
        if is_low_stock:
            query = query.join(MaterialInventory.material).filter(MaterialInventory.quantity_kg < Material.min_stock_level)
            
        inventories = query.order_by(MaterialInventory.warehouse_id, MaterialInventory.material_id).all()

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Bao Cao Ton Kho NVL"

        headers = [
            "Tên Kho", "Vị Trí (Bin/Kệ)", "Mã NVL", "Tên NVL", 
            "Mã Lô (Batch)", "Đơn PO Nhập", "Số Pallet", 
            "Khả dụng (Kg)", "Khả dụng (Cuộn)", "Đã Giữ chỗ (Kg)", "Cập nhật lần cuối"
        ]
        ws.append(headers)

        for cell in ws[1]:
            cell.font = openpyxl.styles.Font(bold=True)

        for inv in inventories:
            wh_name = getattr(inv.warehouse, 'name', None) or getattr(inv.warehouse, 'warehouse_name', str(inv.warehouse_id)) if inv.warehouse else str(inv.warehouse_id)
            mat_code = inv.material.material_code if inv.material else str(inv.material_id)
            mat_name = inv.material.material_name if inv.material else ""
            batch_code = inv.batch.batch_code if inv.batch else str(inv.batch_id)
            
            po_number = "N/A"
            if inv.batch and inv.batch.receipt_detail and inv.batch.receipt_detail.header and getattr(inv.batch.receipt_detail.header, 'po_header', None):
                po_number = getattr(inv.batch.receipt_detail.header.po_header, 'po_number', "N/A")

            ws.append([
                wh_name, inv.location or "",
                mat_code, mat_name, batch_code, po_number,
                inv.number_of_pallets or 0,
                inv.quantity_kg, inv.quantity_cones, inv.reserved_quantity_kg,
                inv.updated_at.strftime("%Y-%m-%d %H:%M") if inv.updated_at else ""
            ])

        stream = io.BytesIO()
        wb.save(stream)
        stream.seek(0)
        return stream

    def create_inventory(self, db: Session, obj_in: MaterialInventoryCreate) -> MaterialInventory:
        db_obj = MaterialInventory(**obj_in.model_dump())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update_inventory(self, db: Session, inventory_id: int, obj_in: MaterialInventoryUpdate) -> Optional[MaterialInventory]:
        db_obj = self.get_inventory(db, inventory_id)
        if not db_obj: return None
            
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
            
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def add_stock(
        self, db: Session, warehouse_id: int, material_id: int, batch_id: int, 
        location: str, qty_kg: float, qty_cones: int, number_of_pallets: int = 0
    ) -> MaterialInventory:
        loc_str = location if location else "N/A"
        
        inventory = db.query(MaterialInventory).filter(
            MaterialInventory.warehouse_id == warehouse_id,
            MaterialInventory.material_id == material_id,
            MaterialInventory.batch_id == batch_id,
            MaterialInventory.location == loc_str
        ).first()

        if inventory:
            inventory.quantity_kg += qty_kg
            inventory.quantity_cones += qty_cones
            if number_of_pallets > 0:
                inventory.number_of_pallets = (inventory.number_of_pallets or 0) + number_of_pallets
        else:
            inventory = MaterialInventory(
                warehouse_id=warehouse_id, material_id=material_id, batch_id=batch_id,
                location=loc_str, quantity_kg=qty_kg, quantity_cones=qty_cones,
                number_of_pallets=number_of_pallets
            )
            db.add(inventory)
            
        db.flush() 
        return inventory

    # ==========================================
    # LOGIC KHỞI TẠO TỒN KHO ĐẦU KỲ (THỦ CÔNG)
    # ==========================================
    def init_stock(self, db: Session, obj_in: InventoryInitStock) -> MaterialInventory:
        # 1. Sinh mã lô nội bộ tự động bằng hàm của material_batch_service
        batch_code = material_batch_service.generate_batch_code(db)
        
        # 2. Tạo bản ghi Lô (Batch)
        new_batch = MaterialBatch(
            batch_code=batch_code,
            material_id=obj_in.material_id,
            supplier_batch_no=obj_in.supplier_batch_no,
            initial_quantity_kg=obj_in.quantity_kg,
            initial_quantity_cones=obj_in.quantity_cones,
            status="Available"
        )
        db.add(new_batch)
        db.flush() # Lấy batch_id ngay lập tức

        # 3. Tạo Tồn kho thực tế
        inventory = self.add_stock(
            db=db,
            warehouse_id=obj_in.warehouse_id,
            material_id=obj_in.material_id,
            batch_id=new_batch.batch_id,
            location=obj_in.location,
            qty_kg=obj_in.quantity_kg,
            qty_cones=obj_in.quantity_cones,
            number_of_pallets=obj_in.number_of_pallets
        )
        
        db.commit()
        db.refresh(inventory)
        return inventory

material_inventory_service = MaterialInventoryService()