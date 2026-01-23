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

    # [UPDATED] Hàm sinh số PO tự động tăng dần: V00000001, V00000002...
    def generate_next_po_number(self) -> str:
        # Tìm số PO lớn nhất hiện tại bắt đầu bằng 'V'
        last_po = self.db.query(PurchaseOrderHeader)\
            .filter(PurchaseOrderHeader.po_number.like("V%"))\
            .order_by(desc(PurchaseOrderHeader.po_number))\
            .first()
        
        if not last_po:
            # Chưa có PO nào, bắt đầu từ 1
            return "V00000001"
        
        try:
            current_code = last_po.po_number
            # Bỏ ký tự 'V' đầu tiên để lấy phần số
            # VD: V00000005 -> 00000005 -> 5
            number_part = int(current_code[1:])
            
            # Tăng lên 1
            next_number = number_part + 1
            
            # Format lại thành chuỗi có 8 chữ số, đệm số 0
            return f"V{next_number:08d}"
        except (ValueError, IndexError):
            # Fallback an toàn nếu dữ liệu cũ không đúng chuẩn
            return "V00000001"

    def create(self, obj_in: POHeaderCreate) -> PurchaseOrderHeader:
        # Tự động sinh số PO nếu không có hoặc là "AUTO"
        if not obj_in.po_number or obj_in.po_number.strip().upper() == "AUTO":
            obj_in.po_number = self.generate_next_po_number()
        
        # Kiểm tra trùng (Double check)
        if self.get_by_number(obj_in.po_number):
            # Nếu trùng do race condition, có thể thử sinh lại hoặc báo lỗi
            raise HTTPException(status_code=400, detail=f"Số PO {obj_in.po_number} đã tồn tại.")

        db_header = PurchaseOrderHeader(
            po_number=obj_in.po_number,
            vendor_id=obj_in.vendor_id,
            order_date=obj_in.order_date,
            expected_arrival_date=obj_in.expected_arrival_date,
            incoterm=obj_in.incoterm,
            currency=obj_in.currency,
            exchange_rate=obj_in.exchange_rate,
            status=obj_in.status,
            note=obj_in.note,
            total_amount=0.0
        )
        self.db.add(db_header)
        self.db.flush()

        total_amount_calc = 0.0
        
        if obj_in.details:
            for detail_in in obj_in.details:
                line_total = detail_in.quantity * detail_in.unit_price
                total_amount_calc += line_total
                
                db_detail = PurchaseOrderDetail(
                    po_id=db_header.po_id,
                    material_id=detail_in.material_id,
                    quantity=detail_in.quantity,
                    unit_price=detail_in.unit_price,
                    uom_id=detail_in.uom_id,
                    line_total=line_total,
                    received_quantity=0.0
                )
                self.db.add(db_detail)

        db_header.total_amount = total_amount_calc
        
        self.db.commit()
        return self.get(db_header.po_id)

    def update(self, db_obj: PurchaseOrderHeader, obj_in: POHeaderUpdate) -> PurchaseOrderHeader:
        update_data = obj_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        self.db.add(db_obj)
        self.db.commit()
        return self.get(db_obj.po_id)

    def add_item(self, po_id: int, item_in: PODetailCreate) -> PurchaseOrderHeader:
        po = self.get(po_id) 
        if not po:
            raise HTTPException(status_code=404, detail="PO not found")

        line_total = item_in.quantity * item_in.unit_price
        
        new_detail = PurchaseOrderDetail(
            po_id=po_id,
            material_id=item_in.material_id,
            quantity=item_in.quantity,
            unit_price=item_in.unit_price,
            uom_id=item_in.uom_id,
            line_total=line_total,
            received_quantity=0.0
        )
        self.db.add(new_detail)
        
        po.total_amount += line_total
        
        self.db.commit()
        return self.get(po_id)
    
    def delete(self, po_id: int):
        db_obj = self.get(po_id)
        if not db_obj:
            raise HTTPException(status_code=404, detail="Đơn hàng không tồn tại.")
        
        # Chỉ cho phép xóa khi đang ở trạng thái Draft (Nháp)
        if db_obj.status != POStatus.DRAFT: # Giả định enum là DRAFT, nếu là Draft thì sửa lại cho khớp model
             raise HTTPException(status_code=400, detail="Chỉ có thể xóa đơn hàng ở trạng thái Nháp (Draft).")

        # Xóa các chi tiết trước (Nếu DB không cấu hình Cascade Delete)
        for detail in db_obj.details:
            self.db.delete(detail)
            
        self.db.delete(db_obj)
        self.db.commit()
        return {"message": "Đã xóa đơn hàng thành công."}