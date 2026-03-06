from sqlalchemy.orm import Session
from sqlalchemy import or_
from fastapi import HTTPException
from typing import Optional
from app.models.po_status import POStatus
from app.schemas.po_status_schema import POStatusCreate, POStatusUpdate

def get_po_statuses(db: Session, search: Optional[str] = None):
    query = db.query(POStatus)
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                POStatus.status_code.ilike(search_term),
                POStatus.description.ilike(search_term)
            )
        )
    return query.all()

def create_po_status(db: Session, status_in: POStatusCreate):
    if db.query(POStatus).filter(POStatus.status_code == status_in.status_code).first():
        raise HTTPException(status_code=409, detail="Mã Trạng thái đã tồn tại.")
        
    db_obj = POStatus(**status_in.model_dump())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def update_po_status(db: Session, status_id: int, status_in: POStatusUpdate):
    db_obj = db.query(POStatus).filter(POStatus.status_id == status_id).first()
    if not db_obj:
        raise HTTPException(status_code=404, detail="Không tìm thấy Trạng thái.")
        
    update_data = status_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_obj, field, value)
        
    db.commit()
    db.refresh(db_obj)
    return db_obj

def delete_po_status(db: Session, status_id: int):
    db_obj = db.query(POStatus).filter(POStatus.status_id == status_id).first()
    if not db_obj:
        raise HTTPException(status_code=404, detail="Không tìm thấy Trạng thái.")
    
    db.delete(db_obj)
    db.commit()
    return {"message": "Đã xóa Trạng thái thành công."}