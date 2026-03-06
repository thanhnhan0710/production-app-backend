from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.po_detail import PurchaseOrderDetail
from app.models.po_header import PurchaseOrderHeader
from app.schemas.po_detail_schema import PurchaseOrderDetailUpdate, PurchaseOrderDetailCreate

def get_po_detail_by_id(db: Session, detail_id: int):
    detail = db.query(PurchaseOrderDetail).filter(PurchaseOrderDetail.detail_id == detail_id).first()
    if not detail:
        raise HTTPException(status_code=404, detail="Không tìm thấy chi tiết đơn hàng.")
    return detail

def create_po_detail(db: Session, po_id: int, detail_in: PurchaseOrderDetailCreate):
    db_header = db.query(PurchaseOrderHeader).filter(PurchaseOrderHeader.po_id == po_id).first()
    if not db_header:
        raise HTTPException(status_code=404, detail="Không tìm thấy Đơn mua hàng cha.")

    if detail_in.is_pricing_by_roll:
        line_total = detail_in.quantity_rolls * detail_in.unit_price
    else:
        line_total = detail_in.quantity_kg * detail_in.unit_price

    # Lọc bỏ exchange_rate
    dump_data = detail_in.model_dump(exclude={"exchange_rate"}, exclude_unset=True)
    db_detail = PurchaseOrderDetail(
        po_id=po_id,
        **dump_data,
        line_total=line_total
    )
    
    db.add(db_detail)
    db.commit()
    db.refresh(db_detail)
    
    _recalculate_header_total(db, po_id)
    return db_detail

def update_po_detail(db: Session, detail_id: int, detail_in: PurchaseOrderDetailUpdate):
    db_detail = get_po_detail_by_id(db, detail_id)
    po_id = db_detail.po_id
    
    update_data = detail_in.model_dump(exclude={"exchange_rate"}, exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_detail, field, value)
        
    recalculate_fields = {"quantity_kg", "quantity_rolls", "unit_price", "is_pricing_by_roll"}
    if any(field in update_data for field in recalculate_fields):
        if db_detail.is_pricing_by_roll:
            db_detail.line_total = db_detail.quantity_rolls * db_detail.unit_price
        else:
            db_detail.line_total = db_detail.quantity_kg * db_detail.unit_price
            
    db.commit()
    db.refresh(db_detail)
    
    _recalculate_header_total(db, po_id)
    return db_detail

def delete_po_detail(db: Session, detail_id: int):
    db_detail = get_po_detail_by_id(db, detail_id)
    po_id = db_detail.po_id
    
    db.delete(db_detail)
    db.commit()
    
    _recalculate_header_total(db, po_id)
    return {"message": "Đã xóa chi tiết đơn hàng thành công."}

def _recalculate_header_total(db: Session, po_id: int):
    db_header = db.query(PurchaseOrderHeader).filter(PurchaseOrderHeader.po_id == po_id).first()
    if not db_header:
        return
        
    # Tính tổng tiền (Thuần USD, bỏ exchange_rate)
    total_usd = sum(detail.line_total for detail in db_header.details)
        
    db_header.total_amount = total_usd
    db.commit()