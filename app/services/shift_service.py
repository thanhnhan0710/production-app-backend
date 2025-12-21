from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.shift import Shift
from app.schemas.shift_schema import ShiftCreate, ShiftUpdate


# =========================
# GET LIST
# =========================
def get_shifts(
    db: Session,
    skip: int = 0,
    limit: int = 100
):
    return (
        db.query(Shift)
        .offset(skip)
        .limit(limit)
        .all()
    )


# =========================
# SEARCH (MÃ / TÊN / GHI CHÚ)
# =========================
def search_shifts(
    db: Session,
    keyword: str,
    skip: int = 0,
    limit: int = 100
):
    return (
        db.query(Shift)
        .filter(
            or_(
                Shift.shift_id.ilike(f"%{keyword}%"),
                Shift.shift_name.ilike(f"%{keyword}%"),
                Shift.note.ilike(f"%{keyword}%")
            )
        )
        .offset(skip)
        .limit(limit)
        .all()
    )


# =========================
# CREATE
# =========================
def create_shift(db: Session, data: ShiftCreate):
    shift = Shift(**data.model_dump())
    db.add(shift)
    db.commit()
    db.refresh(shift)
    return shift


# =========================
# UPDATE (PATCH STYLE)
# =========================
def update_shift(
    db: Session,
    shift_id: int,
    data: ShiftUpdate
):
    shift = db.get(Shift, shift_id)
    if not shift:
        return None

    update_data = data.model_dump(exclude_unset=True)

    for k, v in update_data.items():
        setattr(shift, k, v)

    db.commit()
    db.refresh(shift)
    return shift


# =========================
# DELETE
# =========================
def delete_shift(db: Session, shift_id: int):
    shift = db.get(Shift, shift_id)
    if not shift:
        return False

    db.delete(shift)
    db.commit()
    return True
