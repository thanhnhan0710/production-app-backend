from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException

from app.models.unit import Unit
from app.schemas.unit_schema import UnitCreate, UnitUpdate

def get_units(
    db: Session,
    skip: int = 0,
    limit: int = 100
):
    return (
        db.query(Unit)
        .offset(skip)
        .limit(limit)
        .all()
    )

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
        raise HTTPException(
            status_code=409,
            detail="Unit name already exists"
        )

def update_unit(
    db: Session,
    unit_id: int,
    data: UnitUpdate
):
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
        raise HTTPException(
            status_code=409,
            detail="Unit name already exists"
        )

def search_units(
    db: Session,
    unit_id: Optional[int] = None,
    unit_name: Optional[str] = None,
    note: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
):
    query = db.query(Unit)

    if unit_id:
        query = query.filter(Unit.unit_id == unit_id)

    if unit_name:
        query = query.filter(
            Unit.unit_name.ilike(f"%{unit_name}%")
        )

    # Nếu sau này có cột note
    if note and hasattr(Unit, "note"):
        query = query.filter(
            Unit.note.ilike(f"%{note}%")
        )

    return (
        query
        .offset(skip)
        .limit(limit)
        .all()
    )
