from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.yarn import Yarn
from app.schemas.yarn_schema import YarnCreate, YarnUpdate


# =========================
# GET LIST
# =========================
def get_yarns(db: Session, skip: int = 0, limit: int = 100):
    return (
        db.query(Yarn)
        .offset(skip)
        .limit(limit)
        .all()
    )


# =========================
# SEARCH
# =========================
def search_yarns(
    db: Session,
    keyword: str,
    skip: int = 0,
    limit: int = 100
):
    return (
        db.query(Yarn)
        .filter(
            or_(
                Yarn.yarn_id.ilike(f"%{keyword}%"),
                Yarn.yarn_name.ilike(f"%{keyword}%"),
                Yarn.item_code.ilike(f"%{keyword}%"),
                Yarn.note.ilike(f"%{keyword}%")
            )
        )
        .offset(skip)
        .limit(limit)
        .all()
    )


# =========================
# CREATE
# =========================
def create_yarn(db: Session, yarn: YarnCreate):
    db_yarn = Yarn(**yarn.model_dump())
    db.add(db_yarn)
    db.commit()
    db.refresh(db_yarn)
    return db_yarn


# =========================
# UPDATE
# =========================
def update_yarn(db: Session, yarn_id: int, yarn_data: YarnUpdate):
    db_yarn = db.get(Yarn, yarn_id)
    if not db_yarn:
        return None

    update_data = yarn_data.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(db_yarn, key, value)

    db.commit()
    db.refresh(db_yarn)
    return db_yarn


# =========================
# DELETE
# =========================
def delete_yarn(db: Session, yarn_id: int):
    db_yarn = db.get(Yarn, yarn_id)
    if not db_yarn:
        return False

    db.delete(db_yarn)
    db.commit()
    return True
