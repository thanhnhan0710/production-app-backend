from sqlalchemy.orm import Session
from sqlalchemy import or_
from fastapi import HTTPException
from typing import Optional
from app.models.incoterm import Incoterm
from app.schemas.incoterm_schema import IncotermCreate, IncotermUpdate

def get_incoterms(db: Session, search: Optional[str] = None):
    query = db.query(Incoterm)
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Incoterm.incoterm_code.ilike(search_term),
                Incoterm.description.ilike(search_term)
            )
        )
    return query.all()

def create_incoterm(db: Session, incoterm_in: IncotermCreate):
    if db.query(Incoterm).filter(Incoterm.incoterm_code == incoterm_in.incoterm_code).first():
        raise HTTPException(status_code=409, detail="Mã Incoterm đã tồn tại.")
        
    db_obj = Incoterm(**incoterm_in.model_dump())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def update_incoterm(db: Session, incoterm_id: int, incoterm_in: IncotermUpdate):
    db_obj = db.query(Incoterm).filter(Incoterm.incoterm_id == incoterm_id).first()
    if not db_obj:
        raise HTTPException(status_code=404, detail="Không tìm thấy Incoterm.")
        
    update_data = incoterm_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_obj, field, value)
        
    db.commit()
    db.refresh(db_obj)
    return db_obj

def delete_incoterm(db: Session, incoterm_id: int):
    db_obj = db.query(Incoterm).filter(Incoterm.incoterm_id == incoterm_id).first()
    if not db_obj:
        raise HTTPException(status_code=404, detail="Không tìm thấy Incoterm.")
    
    db.delete(db_obj)
    db.commit()
    return {"message": "Đã xóa Incoterm thành công."}