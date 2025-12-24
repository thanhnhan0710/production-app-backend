from sqlalchemy.orm import Session
from sqlalchemy import desc
from fastapi import HTTPException
from typing import Optional, List
from datetime import datetime

# Import Model & Schema
from app.models.weaving_inspection import WeavingInspection 
from app.models.weaving_basket_ticket import WeavingBasketTicket # Để check tồn tại
from app.schemas.weaving_inspection_schema import WeavingInspectionCreate, WeavingInspectionUpdate

# ============================
# READ (Get Data)
# ============================

def get_inspection_by_id(db: Session, inspection_id: int):
    """Lấy chi tiết 1 lần kiểm tra"""
    return db.query(WeavingInspection).filter(WeavingInspection.id == inspection_id).first()

def get_inspections_by_ticket(db: Session, ticket_id: int, skip: int = 0, limit: int = 100):
    """
    Lấy tất cả các lần kiểm tra của một Phiếu rổ dệt cụ thể.
    Sắp xếp theo thời gian kiểm tra (Mới nhất lên đầu hoặc ngược lại tùy nhu cầu).
    Ở đây để Mới nhất lên đầu (desc).
    """
    return (
        db.query(WeavingInspection)
        .filter(WeavingInspection.weaving_basket_ticket_id == ticket_id)
        .order_by(desc(WeavingInspection.inspection_time))
        .offset(skip)
        .limit(limit)
        .all()
    )

def get_all_inspections(db: Session, skip: int = 0, limit: int = 100):
    """Lấy toàn bộ danh sách kiểm tra (Ít dùng, thường dùng get_by_ticket hơn)"""
    return db.query(WeavingInspection).order_by(desc(WeavingInspection.id)).offset(skip).limit(limit).all()

# ============================
# CREATE
# ============================

def create_inspection(db: Session, inspection_in: WeavingInspectionCreate):
    # 1. Check if Ticket exists (Optional but recommended)
    ticket = db.query(WeavingBasketTicket).filter(WeavingBasketTicket.id == inspection_in.weaving_basket_ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Weaving Basket Ticket not found")

    # 2. Create Object
    db_inspection = WeavingInspection(**inspection_in.model_dump())
    
    # Set default time if not provided
    if not db_inspection.inspection_time:
        db_inspection.inspection_time = datetime.now()

    # 3. Save
    db.add(db_inspection)
    db.commit()
    db.refresh(db_inspection)
    
    return db_inspection

# ============================
# UPDATE
# ============================

def update_inspection(db: Session, inspection_id: int, inspection_in: WeavingInspectionUpdate):
    # 1. Find
    db_inspection = get_inspection_by_id(db, inspection_id)
    if not db_inspection:
        raise HTTPException(status_code=404, detail="Inspection record not found")

    # 2. Check ticket existence if changing ticket_id (Rare case)
    if inspection_in.weaving_basket_ticket_id and inspection_in.weaving_basket_ticket_id != db_inspection.weaving_basket_ticket_id:
        ticket = db.query(WeavingBasketTicket).filter(WeavingBasketTicket.id == inspection_in.weaving_basket_ticket_id).first()
        if not ticket:
             raise HTTPException(status_code=404, detail="New Weaving Basket Ticket not found")

    # 3. Update fields
    update_data = inspection_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_inspection, field, value)

    db.commit()
    db.refresh(db_inspection)
    return db_inspection

# ============================
# DELETE
# ============================

def delete_inspection(db: Session, inspection_id: int):
    db_inspection = get_inspection_by_id(db, inspection_id)
    if not db_inspection:
        raise HTTPException(status_code=404, detail="Inspection record not found")

    db.delete(db_inspection)
    db.commit()
    return {"message": "Inspection record deleted successfully"}