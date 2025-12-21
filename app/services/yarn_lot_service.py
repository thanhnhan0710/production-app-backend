from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.yarn_lot import YarnLot
from datetime import date
from typing import Optional

from app.schemas.yarn_lot_schema import YarnLotCreate, YarnLotUpdate


def get_yarn_lots(db: Session, skip: int = 0, limit: int = 100):
    return (db.query(YarnLot).offset(skip).limit(limit).all())

def get_yarn_lot(db: Session, lot_code: str, yarn_id: int):
    return (
        db.query(YarnLot)
        .filter(
            YarnLot.lot_code == lot_code,
            YarnLot.yarn_id == yarn_id
        )
        .first()
    )

def create_yarn_lot(db: Session, lot_data: YarnLotCreate):
    # Kiểm tra trùng PK
    existing = get_yarn_lot(db, lot_data.lot_code, lot_data.yarn_id)
    if existing:
        raise HTTPException(
            status_code=409,
            detail="Yarn lot already exists"
        )

    db_lot = YarnLot(**lot_data.model_dump())
    db.add(db_lot)
    db.commit()
    db.refresh(db_lot)
    return db_lot

def update_yarn_lot(
    db: Session,
    lot_code: str,
    yarn_id: int,
    lot_data: YarnLotUpdate
):
    db_lot = get_yarn_lot(db, lot_code, yarn_id)
    if not db_lot:
        return None

    update_data = lot_data.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(db_lot, key, value)

    db.commit()
    db.refresh(db_lot)
    return db_lot

def delete_yarn_lot(db: Session, lot_code: str, yarn_id: int):
    db_lot = get_yarn_lot(db, lot_code, yarn_id)
    if not db_lot:
        return False

    db.delete(db_lot)
    db.commit()
    return True

def search_yarn_lots(
    db: Session,
    lot_code: Optional[str] = None,
    yarn_id: Optional[int] = None,
    container_code: Optional[str] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    skip: int = 0,
    limit: int = 100
):
    query = db.query(YarnLot)

    if lot_code:
        query = query.filter(YarnLot.lot_code.ilike(f"%{lot_code}%"))

    if yarn_id:
        query = query.filter(YarnLot.yarn_id == yarn_id)

    if container_code:
        query = query.filter(YarnLot.container_code.ilike(f"%{container_code}%"))

    if from_date:
        query = query.filter(YarnLot.import_date >= from_date)

    if to_date:
        query = query.filter(YarnLot.import_date <= to_date)

    return query.offset(skip).limit(limit).all()
