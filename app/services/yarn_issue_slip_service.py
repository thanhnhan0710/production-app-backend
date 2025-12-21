from sqlalchemy.orm import Session
from sqlalchemy import or_
from datetime import date

from app.models.yarn_issue_slip import YarnIssueSlip
from app.schemas.yarn_issue_slip_schema import (
    YarnIssueSlipCreate,
    YarnIssueSlipUpdate
)


# =========================
# GET LIST
# =========================
def get_issue_slips(
    db: Session,
    skip: int = 0,
    limit: int = 100
):
    return (
        db.query(YarnIssueSlip)
        .offset(skip)
        .limit(limit)
        .all()
    )


# =========================
# GET ONE
# =========================
def get_issue_slip(db: Session, issue_slip_id: int):
    return db.get(YarnIssueSlip, issue_slip_id)


# =========================
# SEARCH (MÃ / NGÀY / GHI CHÚ)
# =========================
def search_issue_slips(
    db: Session,
    keyword: str | None = None,
    issue_date: date | None = None,
    skip: int = 0,
    limit: int = 100
):
    query = db.query(YarnIssueSlip)

    if keyword:
        query = query.filter(
            or_(
                YarnIssueSlip.issue_slip_id.ilike(f"%{keyword}%"),
                YarnIssueSlip.note.ilike(f"%{keyword}%")
            )
        )

    if issue_date:
        query = query.filter(YarnIssueSlip.issue_date == issue_date)

    return (
        query
        .offset(skip)
        .limit(limit)
        .all()
    )


# =========================
# CREATE
# =========================
def create_issue_slip(db: Session, data: YarnIssueSlipCreate):
    slip = YarnIssueSlip(**data.model_dump())
    db.add(slip)
    db.commit()
    db.refresh(slip)
    return slip


# =========================
# UPDATE (PATCH STYLE)
# =========================
def update_issue_slip(
    db: Session,
    issue_slip_id: int,
    data: YarnIssueSlipUpdate
):
    slip = get_issue_slip(db, issue_slip_id)
    if not slip:
        return None

    update_data = data.model_dump(exclude_unset=True)

    for k, v in update_data.items():
        setattr(slip, k, v)

    db.commit()
    db.refresh(slip)
    return slip


# =========================
# DELETE
# =========================
def delete_issue_slip(db: Session, issue_slip_id: int):
    slip = get_issue_slip(db, issue_slip_id)
    if not slip:
        return False

    db.delete(slip)
    db.commit()
    return True
