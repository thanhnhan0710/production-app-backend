from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, desc
from fastapi import HTTPException
from typing import List, Optional
from datetime import date

from app.models.purchase_order import PurchaseOrderHeader, PurchaseOrderDetail, POStatus
from app.schemas.purchase_order_schema import POHeaderCreate, POHeaderUpdate, PODetailCreate

class PurchaseOrderService:
    def __init__(self, db: Session):
        self.db = db

    # ... (Giữ nguyên các hàm get, get_by_number, get_multi, generate_next_po_number) ...
    def get(self, po_id: int) -> Optional[PurchaseOrderHeader]:
        return self.db.query(PurchaseOrderHeader).options(
            joinedload(PurchaseOrderHeader.vendor),
            joinedload(PurchaseOrderHeader.details).joinedload(PurchaseOrderDetail.material),
            joinedload(PurchaseOrderHeader.details).joinedload(PurchaseOrderDetail.uom)
        ).filter(PurchaseOrderHeader.po_id == po_id).first()

    def get_by_number(self, po_number: str) -> Optional[PurchaseOrderHeader]:
        return self.db.query(PurchaseOrderHeader).filter(PurchaseOrderHeader.po_number == po_number).first()

    def get_multi(
        self, 
        skip: int = 0, 
        limit: int = 100, 
        search: str = None,
        vendor_id: int = None,
        status: POStatus = None,
        from_date: date = None,
        to_date: date = None
    ) -> List[PurchaseOrderHeader]:
        query = self.db.query(PurchaseOrderHeader).options(
            joinedload(PurchaseOrderHeader.vendor) 
        )

        if vendor_id:
            query = query.filter(PurchaseOrderHeader.vendor_id == vendor_id)
        
        if status:
            query = query.filter(PurchaseOrderHeader.status == status)

        if from_date:
            query = query.filter(PurchaseOrderHeader.order_date >= from_date)
        
        if to_date:
            query = query.filter(PurchaseOrderHeader.order_date <= to_date)

        if search:
            query = query.filter(PurchaseOrderHeader.po_number.ilike(f"%{search}%"))

        return query.order_by(PurchaseOrderHeader.order_date.desc()).offset(skip).limit(limit).all()

    def generate_next_po_number(self) -> str:
        last_po = self.db.query(PurchaseOrderHeader)\
            .filter(PurchaseOrderHeader.po_number.like("V%"))\
            .order_by(desc(PurchaseOrderHeader.po_number))\
            .first()
        
        if not last_po:
            return "V00000001"
        
        try:
            current_code = last_po.po_number
            number_part = int(current_code[1:])
            next_number = number_part + 1
            return f"V{next_number:08d}"
        except (ValueError, IndexError):
            return "V00000001"

    # [UPDATED] Hàm tạo PO
    def create(self, obj_in: POHeaderCreate) -> PurchaseOrderHeader:
        if not obj_in.po_number or obj_in.po_number.strip().upper() == "AUTO":
            obj_in.po_number = self.generate_next_po_number()
        
        if self.get_by_number(obj_in.po_number):
            raise HTTPException(status_code=400, detail=f"Số PO {obj_in.po_number} đã tồn tại.")

        db_header = PurchaseOrderHeader(
            po_number=obj_in.po_number,
            vendor_id=obj_in.vendor_id,
            order_date=obj_in.order_date,
            expected_arrival_date=obj_in.expected_arrival_date,
            incoterm=obj_in.incoterm,
            currency=obj_in.currency,
            exchange_rate=obj_in.exchange_rate,
            
            # [UPDATED] Sử dụng status gửi lên từ FE (nếu có), mặc định là Draft
            status=obj_in.status or POStatus.DRAFT, 
            
            note=obj_in.note,
            total_amount=0.0
        )
        self.db.add(db_header)
        self.db.flush()

        total_amount_calc = 0.0
        
        if obj_in.details:
            for detail_in in obj_in.details:
                # [LOGIC MỚI] Tính tiền dựa trên cờ is_pricing_by_roll
                if detail_in.is_pricing_by_roll:
                    # Nếu tính theo cuộn: Số cuộn * Đơn giá
                    line_total = (detail_in.quantity_rolls or 0) * detail_in.unit_price
                else:
                    # Mặc định: Số Kg * Đơn giá
                    line_total = detail_in.quantity * detail_in.unit_price
                
                total_amount_calc += line_total
                
                db_detail = PurchaseOrderDetail(
                    po_id=db_header.po_id,
                    material_id=detail_in.material_id,
                    quantity=detail_in.quantity,
                    quantity_rolls=detail_in.quantity_rolls,
                    unit_price=detail_in.unit_price,
                    uom_id=detail_in.uom_id,
                    
                    line_total=line_total,           # Lưu tổng tiền đã tính
                    is_pricing_by_roll=detail_in.is_pricing_by_roll, # Lưu cờ
                    
                    received_quantity=0.0,
                    received_rolls=0
                )
                self.db.add(db_detail)

        db_header.total_amount = total_amount_calc
        
        self.db.commit()
        return self.get(db_header.po_id)

    # [UPDATED] Update header cũng cần tính lại total nếu details thay đổi (tuy nhiên hàm này chỉ update header info)
    def update(self, db_obj: PurchaseOrderHeader, obj_in: POHeaderUpdate) -> PurchaseOrderHeader:
        # 1. Cập nhật thông tin Header
        update_data = obj_in.dict(exclude_unset=True)
        
        # Tách phần details ra xử lý riêng
        details_in = update_data.pop("details", None)

        for field, value in update_data.items():
            setattr(db_obj, field, value)

        # 2. Xử lý cập nhật Details (Nếu có gửi lên)
        if details_in is not None:
            # Cách xử lý: Xóa hết chi tiết cũ -> Tạo lại chi tiết mới
            # Lưu ý: Chỉ nên làm vậy khi PO chưa nhập kho (received_quantity = 0)
            
            # Xóa chi tiết cũ
            for old_detail in db_obj.details:
                self.db.delete(old_detail)
            
            # Flush để lệnh xóa có hiệu lực trước khi thêm mới
            self.db.flush() 

            total_amount_calc = 0.0
            
            # Tạo chi tiết mới
            for item in details_in:
                # Ép kiểu item về object (vì pop ra có thể là dict hoặc model tùy context)
                if isinstance(item, dict):
                    # Nếu là dict thì truy cập theo key
                    is_roll = item.get('is_pricing_by_roll', False)
                    q_rolls = item.get('quantity_rolls', 0)
                    qty = item.get('quantity', 0)
                    price = item.get('unit_price', 0)
                    mat_id = item.get('material_id')
                    uom_id = item.get('uom_id')
                else:
                    # Nếu là Pydantic model
                    is_roll = item.is_pricing_by_roll
                    q_rolls = item.quantity_rolls
                    qty = item.quantity
                    price = item.unit_price
                    mat_id = item.material_id
                    uom_id = item.uom_id

                # Tính line_total
                if is_roll:
                    line_total = (q_rolls or 0) * price
                else:
                    line_total = qty * price
                
                total_amount_calc += line_total

                new_detail = PurchaseOrderDetail(
                    po_id=db_obj.po_id, # Link với ID cũ
                    material_id=mat_id,
                    quantity=qty,
                    quantity_rolls=q_rolls,
                    unit_price=price,
                    uom_id=uom_id,
                    line_total=line_total,
                    is_pricing_by_roll=is_roll,
                    received_quantity=0.0,
                    received_rolls=0
                )
                self.db.add(new_detail)
            
            # Cập nhật lại tổng tiền Header
            db_obj.total_amount = total_amount_calc

        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return self.get(db_obj.po_id)

    # [UPDATED] Hàm thêm dòng mới
    def add_item(self, po_id: int, item_in: PODetailCreate) -> PurchaseOrderHeader:
        po = self.get(po_id) 
        if not po:
            raise HTTPException(status_code=404, detail="PO not found")

        # [LOGIC MỚI] Tính tiền
        if item_in.is_pricing_by_roll:
            line_total = (item_in.quantity_rolls or 0) * item_in.unit_price
        else:
            line_total = item_in.quantity * item_in.unit_price
        
        new_detail = PurchaseOrderDetail(
            po_id=po_id,
            material_id=item_in.material_id,
            quantity=item_in.quantity,
            quantity_rolls=item_in.quantity_rolls,
            unit_price=item_in.unit_price,
            uom_id=item_in.uom_id,
            
            line_total=line_total,
            is_pricing_by_roll=item_in.is_pricing_by_roll, # Lưu cờ
            
            received_quantity=0.0,
            received_rolls=0
        )
        self.db.add(new_detail)
        
        # Cập nhật tổng tiền PO
        po.total_amount += line_total
        
        self.db.commit()
        return self.get(po_id)
    
    # ... (Giữ nguyên hàm delete) ...
    def delete(self, po_id: int):
        db_obj = self.get(po_id)
        if not db_obj:
            raise HTTPException(status_code=404, detail="Đơn hàng không tồn tại.")
        
        if db_obj.status != POStatus.DRAFT:
             raise HTTPException(status_code=400, detail="Chỉ có thể xóa đơn hàng ở trạng thái Nháp (Draft).")

        for detail in db_obj.details:
            self.db.delete(detail)
            
        self.db.delete(db_obj)
        self.db.commit()
        return {"message": "Đã xóa đơn hàng thành công."}