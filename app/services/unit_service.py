from operator import or_
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException

from app.models.unit import Unit
from app.schemas.unit_schema import UnitCreate, UnitUpdate

def get_units(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Unit).offset(skip).limit(limit).all()

def get_unit(db: Session, unit_id: int):
    return db.get(Unit, unit_id)

def create_unit(db: Session, data: UnitCreate):
    try:
        unit = Unit(**data.model_dump())
        db.add(unit)
        db.commit()
        db.refresh(unit)
        return unit
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Unit name already exists")

def update_unit(db: Session, unit_id: int, data: UnitUpdate):
    unit = db.get(Unit, unit_id)
    if not unit:
        return None

    update_data = data.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(unit, key, value)

    try:
        db.commit()
        db.refresh(unit)
        return unit
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Unit name already exists")

# [MỚI] Hàm xóa đơn vị
def delete_unit(db: Session, unit_id: int):
    unit = db.get(Unit, unit_id)
    if not unit:
        return False
    
    try:
        db.delete(unit)
        db.commit()
        return True
    except IntegrityError:
        db.rollback()
        # Trả về lỗi 400 nếu đơn vị đang được sử dụng ở bảng Material
        raise HTTPException(
            status_code=400, 
            detail="Cannot delete this unit because it is referenced by other records (e.g., Materials)."
        )

def search_units(db: Session, keyword: str, skip: int = 0, limit: int = 100):
    query = db.query(Unit)
    if keyword.isdigit():
        query = query.filter(or_(Unit.unit_id == int(keyword)))
    else:
        query = query.filter(
            or_(
                Unit.unit_name.ilike(f"%{keyword}%"),
                Unit.note.ilike(f"%{keyword}%"),
            )
        )
    return query.offset(skip).limit(limit).all()