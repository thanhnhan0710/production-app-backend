from sqlalchemy.orm import Session
from sqlalchemy import or_, desc
from fastapi import HTTPException
from typing import List, Optional
from datetime import datetime
import time

# Models
from app.models.material_export import MaterialExport, MaterialExportDetail
from app.models.weaving_basket_ticket import WeavingBasketTicket
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

    # ============================
    # GET / SEARCH
    # ============================
    def get(self, export_id: int) -> Optional[MaterialExport]:
        return self.db.query(MaterialExport).filter(MaterialExport.id == export_id).first()

    def get_multi(self, skip: int = 0, limit: int = 100, filter_param: Optional[MaterialExportFilter] = None):
        query = self.db.query(MaterialExport)
        
        if filter_param:
            if filter_param.warehouse_id:
                query = query.filter(MaterialExport.warehouse_id == filter_param.warehouse_id)
            if filter_param.receiver_id:
                query = query.filter(MaterialExport.receiver_id == filter_param.receiver_id)
            if filter_param.from_date:
                query = query.filter(MaterialExport.export_date >= filter_param.from_date)
            if filter_param.to_date:
                query = query.filter(MaterialExport.export_date <= filter_param.to_date)
            if filter_param.search:
                term = f"%{filter_param.search}%"
                query = query.filter(
                    or_(
                        MaterialExport.export_code.ilike(term),
                        MaterialExport.note.ilike(term)
                    )
                )

        return query.order_by(desc(MaterialExport.export_date)).offset(skip).limit(limit).all()

    # ============================
    # CREATE (Tạo phiếu xuất & Xử lý logic kho/sản xuất)
    # ============================
    def create_export(self, obj_in: MaterialExportCreate) -> MaterialExport:
        # 1. Tạo Header Phiếu Xuất
        db_export = MaterialExport(
            export_code=obj_in.export_code,
            export_date=obj_in.export_date or datetime.now().date(),
            warehouse_id=obj_in.warehouse_id,
            department_id=obj_in.department_id,
            receiver_id=obj_in.receiver_id,
            shift_id=obj_in.shift_id,
            note=obj_in.note,
            created_by=obj_in.created_by
        )
        self.db.add(db_export)
        self.db.flush() # Flush để lấy ID phiếu xuất

        # 2. Xử lý từng dòng chi tiết
        for detail_in in obj_in.details:
            
            # --- VALIDATION: KIỂM TRA RỔ ---
            if detail_in.basket_id:
                basket = self.db.query(Basket).get(detail_in.basket_id)
                if not basket:
                    raise HTTPException(status_code=404, detail=f"Không tìm thấy Rổ ID {detail_in.basket_id}")
                if basket.status != BasketStatus.READY:
                    raise HTTPException(status_code=400, detail=f"Rổ {basket.basket_code} không sẵn sàng (Trạng thái: {basket.status})")

            # --- VALIDATION: KIỂM TRA MÁY VÀ LINE ---
            if detail_in.machine_id and detail_in.machine_line:
                # Kiểm tra xem máy/line này có đang chạy phiếu nào khác không
                existing_ticket = self.db.query(WeavingBasketTicket).filter(
                    WeavingBasketTicket.machine_id == detail_in.machine_id,
                    WeavingBasketTicket.machine_line == detail_in.machine_line,
                    WeavingBasketTicket.time_out.is_(None) # Chưa kết thúc
                ).first()
                
                if existing_ticket:
                     raise HTTPException(
                        status_code=400, 
                        detail=f"Máy {detail_in.machine_id} Line {detail_in.machine_line} đang hoạt động. Vui lòng hạ rổ trước."
                    )

            # --- A. TẠO DETAIL XUẤT KHO ---
            db_detail = MaterialExportDetail(
                export_id=db_export.id,
                material_id=detail_in.material_id,
                batch_id=detail_in.batch_id,
                quantity=detail_in.quantity,
                
                # Thông tin sản xuất
                machine_id=detail_in.machine_id,
                machine_line=detail_in.machine_line,
                product_id=detail_in.product_id,
                standard_id=detail_in.standard_id,
                basket_id=detail_in.basket_id,
                
                note=detail_in.note
            )
            self.db.add(db_detail)

            # --- B. TRỪ TỒN KHO ---
            try:
                # Kiểm tra số lượng tồn trước
                stock = self.inventory_service.get_stock_by_batch(obj_in.warehouse_id, detail_in.batch_id)
                current_qty = stock.quantity_on_hand if stock else 0.0
                
                if current_qty < detail_in.quantity:
                    raise HTTPException(
                        status_code=400, 
                        detail=f"Không đủ tồn kho cho Batch ID {detail_in.batch_id}. Tồn: {current_qty}, Xuất: {detail_in.quantity}"
                    )

                # Gọi hàm trừ kho (truyền số âm)
                self.inventory_service.increase_stock(
                    material_id=detail_in.material_id,
                    warehouse_id=obj_in.warehouse_id,
                    batch_id=detail_in.batch_id,
                    quantity= -detail_in.quantity 
                )
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Lỗi kho: {str(e)}")

            # --- C. TỰ ĐỘNG TẠO PHIẾU RỔ DỆT ---
            if (detail_in.machine_id and detail_in.product_id and 
                detail_in.basket_id and detail_in.standard_id):
                
                self._create_auto_weaving_ticket(
                    header_in=obj_in,
                    detail_in=detail_in
                )
                
                # Cập nhật trạng thái rổ -> IN_USE
                # Lưu ý: Query lại basket để đảm bảo session track đúng object
                basket_to_update = self.db.query(Basket).get(detail_in.basket_id)
                if basket_to_update:
                    basket_to_update.status = BasketStatus.IN_USE
                    self.db.add(basket_to_update)

        # 3. COMMIT TOÀN BỘ
        try:
            self.db.commit()
            self.db.refresh(db_export)
            return db_export # [QUAN TRỌNG] Trả về object để FastAPI serialize
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Lỗi hệ thống khi lưu phiếu xuất: {str(e)}")

    def _create_auto_weaving_ticket(self, header_in: MaterialExportCreate, detail_in):
        """Hàm nội bộ: Sinh phiếu rổ dệt"""
        timestamp = int(time.time())
        ticket_code = f"WBT-{detail_in.basket_id}-{timestamp}"
        yarn_lot_id = detail_in.batch_id 

        new_ticket = WeavingBasketTicket(
            code=ticket_code,
            product_id=detail_in.product_id,
            standard_id=detail_in.standard_id,
            machine_id=detail_in.machine_id,
            machine_line=detail_in.machine_line,
            
            yarn_load_date=header_in.export_date,
            batch_id=detail_in.batch_id,
            basket_id=detail_in.basket_id,
            
            time_in=datetime.now(),
            employee_in_id=header_in.receiver_id,
            
            number_of_knots=0,
            gross_weight=0.0,
            net_weight=0.0,
            length_meters=0.0
        )
        self.db.add(new_ticket)

    # ============================
    # UPDATE
    # ============================
    def update(self, export_id: int, obj_in: MaterialExportUpdate) -> MaterialExport:
        db_obj = self.get(export_id)
        if not db_obj:
            raise HTTPException(status_code=404, detail="Phiếu xuất không tồn tại")
        
        update_data = obj_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    # ============================
    # DELETE (Hủy phiếu)
    # ============================
    def delete(self, export_id: int):
        db_obj = self.get(export_id)
        if not db_obj:
            raise HTTPException(status_code=404, detail="Phiếu xuất không tồn tại")

        # Duyệt qua các dòng chi tiết để hoàn tác
        for detail in db_obj.details:
            # 1. HOÀN TRẢ TỒN KHO
            self.inventory_service.increase_stock(
                material_id=detail.material_id,
                warehouse_id=db_obj.warehouse_id,
                batch_id=detail.batch_id,
                quantity=detail.quantity # Cộng số dương để trả lại kho
            )

            # 2. HỦY PHIẾU RỔ DỆT & TRẢ RỔ VỀ READY
            if detail.basket_id:
                # Tìm phiếu rổ đang chạy (time_out is None)
                ticket = self.db.query(WeavingBasketTicket).filter(
                    WeavingBasketTicket.basket_id == detail.basket_id,
                    WeavingBasketTicket.time_out.is_(None)
                ).first()

                if ticket:
                    # Kiểm tra xem phiếu này đã sản xuất chưa
                    if ticket.gross_weight and ticket.gross_weight > 0:
                        raise HTTPException(
                            status_code=400, 
                            detail=f"Không thể hủy phiếu xuất. Rổ {detail.basket_id} đã có ghi nhận sản lượng."
                        )
                    self.db.delete(ticket)
                
                # Trả trạng thái rổ về READY
                basket = self.db.query(Basket).get(detail.basket_id)
                if basket:
                    basket.status = BasketStatus.READY
                    self.db.add(basket)

        # Xóa Header
        self.db.delete(db_obj)
        self.db.commit()
        return {"message": "Đã hủy phiếu xuất thành công."}