from sqlalchemy.orm import Session
from sqlalchemy import or_, desc
from fastapi import HTTPException
from typing import List, Optional
from datetime import datetime
import time

# Models
from app.models.material_export import MaterialExport, MaterialExportDetail
from app.models.weaving_basket_ticket import WeavingBasketTicket, WeavingTicketYarn
from app.models.basket import Basket, BasketStatus

# Schemas
from app.schemas.material_export_schema import (
    MaterialExportCreate, 
    MaterialExportUpdate, 
    MaterialExportFilter
)

# Services
from app.services.inventory_service import InventoryService

class MaterialExportService:
    def __init__(self, db: Session):
        self.db = db
        self.inventory_service = InventoryService(db)

    # ... (Các hàm generate_code, get, get_multi giữ nguyên không đổi) ...
    
    def generate_next_export_code(self) -> str:
        now = datetime.now()
        prefix = now.strftime("%Y%m")
        last_export = self.db.query(MaterialExport)\
            .filter(MaterialExport.export_code.like(f"{prefix}-%"))\
            .order_by(desc(MaterialExport.export_code))\
            .first()
        if not last_export:
            return f"{prefix}-0001"
        try:
            last_code = last_export.export_code
            parts = last_code.split('-')
            last_seq = int(parts[1]) 
            new_seq = last_seq + 1 
            return f"{prefix}-{new_seq:04d}"
        except (IndexError, ValueError):
            return f"{prefix}-0001"

    def get(self, export_id: int) -> Optional[MaterialExport]:
        return self.db.query(MaterialExport).filter(MaterialExport.id == export_id).first()

    def get_multi(self, skip: int = 0, limit: int = 100, filter_param: Optional[MaterialExportFilter] = None):
        query = self.db.query(MaterialExport)
        if filter_param:
            if filter_param.warehouse_id:
                query = query.filter(MaterialExport.warehouse_id == filter_param.warehouse_id)
            if filter_param.exporter_id:
                query = query.filter(MaterialExport.exporter_id == filter_param.exporter_id)
            if filter_param.receiver_id:
                query = query.filter(MaterialExport.receiver_id == filter_param.receiver_id)
            if filter_param.from_date:
                query = query.filter(MaterialExport.export_date >= filter_param.from_date)
            if filter_param.to_date:
                query = query.filter(MaterialExport.export_date <= filter_param.to_date)
            if filter_param.search:
                term = f"%{filter_param.search}%"
                query = query.filter(or_(MaterialExport.export_code.ilike(term), MaterialExport.note.ilike(term)))
        return query.order_by(desc(MaterialExport.export_date)).offset(skip).limit(limit).all()

    # ============================
    # CREATE
    # ============================
    def create_export(self, obj_in: MaterialExportCreate) -> MaterialExport:
        if not obj_in.export_code or obj_in.export_code.strip().upper() == "AUTO":
            obj_in.export_code = self.generate_next_export_code()

        existing = self.db.query(MaterialExport).filter(MaterialExport.export_code == obj_in.export_code).first()
        if existing:
             raise HTTPException(status_code=400, detail=f"Mã phiếu xuất {obj_in.export_code} đã tồn tại.")

        # 1. Tạo Header
        db_export = MaterialExport(
            export_code=obj_in.export_code,
            export_date=obj_in.export_date or datetime.now().date(),
            warehouse_id=obj_in.warehouse_id,
            department_id=obj_in.department_id,
            exporter_id=obj_in.exporter_id,
            receiver_id=obj_in.receiver_id,
            shift_id=obj_in.shift_id,
            note=obj_in.note,
            created_by=obj_in.created_by
        )
        self.db.add(db_export)
        self.db.flush() 

        # 2. Xử lý chi tiết
        for detail_in in obj_in.details:
            
            # Xử lý 0 -> None
            basket_id_val = detail_in.basket_id if detail_in.basket_id and detail_in.basket_id > 0 else None
            standard_id_val = detail_in.standard_id if detail_in.standard_id and detail_in.standard_id > 0 else None

            # --- VALIDATION RỔ ---
            if basket_id_val:
                basket = self.db.query(Basket).get(basket_id_val)
                if not basket:
                    raise HTTPException(status_code=404, detail=f"Không tìm thấy Rổ ID {basket_id_val}")
                if basket.status != BasketStatus.READY:
                    raise HTTPException(status_code=400, detail=f"Rổ {basket.basket_code} không sẵn sàng (Trạng thái: {basket.status})")

            # --- A. TẠO DETAIL ---
            db_detail = MaterialExportDetail(
                export_id=db_export.id,
                material_id=detail_in.material_id,
                batch_id=detail_in.batch_id,
                quantity=detail_in.quantity,
                
                # Lưu loại sợi
                component_type=detail_in.component_type, 

                machine_id=detail_in.machine_id,
                machine_line=detail_in.machine_line,
                product_id=detail_in.product_id,
                
                standard_id=standard_id_val,
                basket_id=basket_id_val,
                
                note=detail_in.note
            )
            self.db.add(db_detail)

            # --- B. TRỪ KHO ---
            try:
                stock = self.inventory_service.get_stock_by_batch(obj_in.warehouse_id, detail_in.batch_id)
                current_qty = stock.quantity_on_hand if stock else 0.0
                
                if current_qty < detail_in.quantity:
                    raise HTTPException(status_code=400, detail=f"Không đủ tồn kho Batch {detail_in.batch_id}. Tồn: {current_qty}")

                self.inventory_service.increase_stock(
                    material_id=detail_in.material_id,
                    warehouse_id=obj_in.warehouse_id,
                    batch_id=detail_in.batch_id,
                    quantity= -detail_in.quantity 
                )
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Lỗi kho: {str(e)}")

            # --- C. TẠO HOẶC CẬP NHẬT PHIẾU RỔ DỆT ---
            if (detail_in.machine_id and detail_in.product_id):
                
                # Logic: Tìm Ticket đang "mở" (vừa tạo hoặc đang chạy) hoặc tạo mới.
                self._ensure_weaving_ticket_and_add_yarn(
                    header_in=obj_in,
                    detail_in=detail_in,
                    real_basket_id=basket_id_val,
                    real_standard_id=standard_id_val,
                    yarn_quantity=detail_in.quantity # [UPDATED] Truyền số lượng xuất
                )
                
                if basket_id_val:
                    basket_to_update = self.db.query(Basket).get(basket_id_val)
                    if basket_to_update:
                        basket_to_update.status = BasketStatus.IN_USE
                        self.db.add(basket_to_update)

        try:
            self.db.commit()
            self.db.refresh(db_export)
            return db_export 
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Lỗi hệ thống: {str(e)}")

    # [UPDATED LOGIC] Xử lý tạo ticket và add yarn
    def _ensure_weaving_ticket_and_add_yarn(self, header_in, detail_in, real_basket_id, real_standard_id, yarn_quantity: float):
        """
        Tìm ticket đang chạy (hoặc vừa tạo trong session) cho máy/line này.
        Nếu chưa có -> Tạo mới Ticket.
        Sau đó -> Thêm dòng vào WeavingTicketYarn.
        """
        # 1. Tìm Ticket đang hoạt động (time_out IS NULL)
        current_ticket = self.db.query(WeavingBasketTicket).filter(
            WeavingBasketTicket.machine_id == detail_in.machine_id,
            WeavingBasketTicket.machine_line == detail_in.machine_line,
            WeavingBasketTicket.time_out.is_(None)
        ).first()

        if not current_ticket:
            # Chưa có ticket (máy đang dừng) -> Tạo mới Header Ticket
            timestamp = int(time.time())
            ticket_code = f"WBT-{real_basket_id}-{timestamp}-{detail_in.machine_id}" 
            
            current_ticket = WeavingBasketTicket(
                code=ticket_code,
                product_id=detail_in.product_id,
                standard_id=real_standard_id,
                machine_id=detail_in.machine_id,
                machine_line=detail_in.machine_line,
                yarn_load_date=header_in.export_date,
                basket_id=real_basket_id,
                time_in=datetime.now(),
                employee_in_id=None,
                number_of_knots=0,
                gross_weight=0.0,
                net_weight=0.0,
                length_meters=0.0
            )
            self.db.add(current_ticket)
            self.db.flush() # Để có ID cho bảng con

        # 2. Thêm dòng vào bảng WeavingTicketYarn (Quan hệ 1-N)
        # Đây là nơi Batch mới được thêm vào Ticket cũ (nếu máy đang chạy)
        new_yarn_link = WeavingTicketYarn(
            ticket_id=current_ticket.id,
            batch_id=detail_in.batch_id,
            component_type=detail_in.component_type or "UNKNOWN",
            quantity=yarn_quantity, # [UPDATED] Lưu số lượng xuất vào bảng yarn
            note=detail_in.note
        )
        self.db.add(new_yarn_link)

    def update(self, export_id: int, obj_in: MaterialExportUpdate) -> MaterialExport:
        db_obj = self.get(export_id)
        if not db_obj: raise HTTPException(status_code=404, detail="Phiếu không tồn tại")
        update_data = obj_in.dict(exclude_unset=True)
        for field, value in update_data.items(): setattr(db_obj, field, value)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def delete(self, export_id: int):
        db_obj = self.get(export_id)
        if not db_obj: raise HTTPException(status_code=404, detail="Phiếu không tồn tại")
        for detail in db_obj.details:
            self.inventory_service.increase_stock(
                material_id=detail.material_id,
                warehouse_id=db_obj.warehouse_id,
                batch_id=detail.batch_id,
                quantity=detail.quantity 
            )
            
            if detail.basket_id:
                ticket = self.db.query(WeavingBasketTicket).filter(
                    WeavingBasketTicket.basket_id == detail.basket_id,
                    WeavingBasketTicket.time_out.is_(None)
                ).first()
                if ticket:
                    if ticket.gross_weight and ticket.gross_weight > 0:
                        raise HTTPException(status_code=400, detail=f"Rổ {detail.basket_id} đã sản xuất, không thể hủy.")
                    
                    # Cascade delete sẽ tự xóa dòng trong weaving_ticket_yarns
                    self.db.delete(ticket)
                
                basket = self.db.query(Basket).get(detail.basket_id)
                if basket:
                    basket.status = BasketStatus.READY
                    self.db.add(basket)
        
        self.db.delete(db_obj)
        self.db.commit()
        return {"message": "Đã hủy phiếu xuất thành công."}