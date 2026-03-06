import math
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc
from fastapi import HTTPException
from typing import Optional

from app.models.po_header import PurchaseOrderHeader
from app.models.po_detail import PurchaseOrderDetail
from app.models.supplier import Supplier
from app.models.material import Material
from app.schemas.po_header_schema import PurchaseOrderHeaderCreate, PurchaseOrderHeaderUpdate

def get_next_po_number(db: Session) -> str:
    last_po = db.query(PurchaseOrderHeader).filter(
        PurchaseOrderHeader.po_number.like('V%')
    ).order_by(desc(PurchaseOrderHeader.po_number)).first()
    
    if last_po and len(last_po.po_number) >= 9:
        try:
            last_num = int(last_po.po_number[1:])
            return f"V{last_num + 1:08d}"
        except ValueError:
            pass
    return "V00000001"

# [ĐÃ SỬA]: Thêm tham số status_id vào hàm get
def get_purchase_orders(db: Session, skip: int = 0, limit: int = 100, vendor_id: Optional[int] = None, status_id: Optional[int] = None, search: Optional[str] = None):
    query = db.query(PurchaseOrderHeader).options(joinedload(PurchaseOrderHeader.details))
    if vendor_id:
        query = query.filter(PurchaseOrderHeader.vendor_id == vendor_id)
    if status_id:
        query = query.filter(PurchaseOrderHeader.status_id == status_id)
    if search:
        query = query.filter(PurchaseOrderHeader.po_number.ilike(f"%{search}%"))
    return query.order_by(desc(PurchaseOrderHeader.created_at)).offset(skip).limit(limit).all()

# [ĐÃ SỬA]: Thêm tham số status_id vào hàm count
def count_purchase_orders(db: Session, vendor_id: Optional[int] = None, status_id: Optional[int] = None, search: Optional[str] = None):
    query = db.query(PurchaseOrderHeader)
    if vendor_id:
        query = query.filter(PurchaseOrderHeader.vendor_id == vendor_id)
    if status_id:
        query = query.filter(PurchaseOrderHeader.status_id == status_id)
    if search:
        query = query.filter(PurchaseOrderHeader.po_number.ilike(f"%{search}%"))
    return query.count()

def get_po_by_id(db: Session, po_id: int):
    po = db.query(PurchaseOrderHeader).options(joinedload(PurchaseOrderHeader.details)).filter(PurchaseOrderHeader.po_id == po_id).first()
    if not po:
        raise HTTPException(status_code=404, detail="Không tìm thấy Đơn mua hàng.")
    return po

def create_purchase_order(db: Session, po_in: PurchaseOrderHeaderCreate):
    if not po_in.po_number or "đang tải" in po_in.po_number.lower() or po_in.po_number == "AUTO":
        po_in.po_number = get_next_po_number(db)

    if db.query(PurchaseOrderHeader).filter(PurchaseOrderHeader.po_number == po_in.po_number).first():
        raise HTTPException(status_code=409, detail="Số PO đã tồn tại trong hệ thống.")

    if not db.query(Supplier).filter(Supplier.supplier_id == po_in.vendor_id).first():
        raise HTTPException(status_code=400, detail="Nhà cung cấp không hợp lệ.")

    total_amount_vnd = 0.0
    details_db = []
    
    for d in po_in.details:
        mat = db.query(Material).filter(Material.material_id == d.material_id).first()
        qty_rolls = d.quantity_rolls
        if qty_rolls == 0 and mat and mat.kg_per_bobbin and mat.kg_per_bobbin > 0:
            qty_rolls = math.ceil(d.quantity_kg / mat.kg_per_bobbin)

        if d.is_pricing_by_roll:
            line_total = qty_rolls * d.unit_price
        else:
            line_total = d.quantity_kg * d.unit_price
            
        total_amount_vnd += (line_total * d.exchange_rate)
        
        detail_obj = PurchaseOrderDetail(
            **d.model_dump(exclude={"quantity_rolls"}),
            quantity_rolls=qty_rolls,
            line_total=line_total
        )
        details_db.append(detail_obj)

    header_data = po_in.model_dump(exclude={"details"})
    db_po = PurchaseOrderHeader(**header_data, total_amount=total_amount_vnd)
    db_po.details = details_db
    
    db.add(db_po)
    db.commit()
    db.refresh(db_po)
    return db_po

def update_po_header(db: Session, po_id: int, po_update: PurchaseOrderHeaderUpdate):
    db_po = get_po_by_id(db, po_id)
    update_data = po_update.model_dump(exclude_unset=True)
    
    if "po_number" in update_data and update_data["po_number"] != db_po.po_number:
        if db.query(PurchaseOrderHeader).filter(PurchaseOrderHeader.po_number == update_data["po_number"]).first():
            raise HTTPException(status_code=409, detail="Số PO đã tồn tại.")
            
    for field, value in update_data.items():
        if field != "details":
            setattr(db_po, field, value)
            
    if "details" in update_data:
        db_po.details.clear() 
        total_amount_vnd = 0.0
        new_details = []
        for d in update_data["details"]:
            mat = db.query(Material).filter(Material.material_id == d['material_id']).first()
            qty_rolls = d.get('quantity_rolls', 0)
            if qty_rolls == 0 and mat and mat.kg_per_bobbin and mat.kg_per_bobbin > 0:
                qty_rolls = math.ceil(d['quantity_kg'] / mat.kg_per_bobbin)

            is_roll_price = d.get('is_pricing_by_roll', False)
            line_total = qty_rolls * d['unit_price'] if is_roll_price else d['quantity_kg'] * d['unit_price']
            total_amount_vnd += (line_total * d.get('exchange_rate', 1.0))
            
            new_detail = PurchaseOrderDetail(
                material_id=d['material_id'],
                currency=d.get('currency', 'VND'),
                exchange_rate=d.get('exchange_rate', 1.0),
                quantity_kg=d['quantity_kg'],
                quantity_rolls=qty_rolls,
                unit_price=d['unit_price'],
                is_pricing_by_roll=is_roll_price,
                line_total=line_total
            )
            new_details.append(new_detail)
            
        db_po.details = new_details
        db_po.total_amount = total_amount_vnd
        
    db.commit()
    db.refresh(db_po)
    return db_po

def delete_po_header(db: Session, po_id: int):
    db_po = get_po_by_id(db, po_id)
    db.delete(db_po)
    db.commit()
    return {"message": "Đã xóa Đơn mua hàng thành công."}