from sqlalchemy.orm import Session
from app.models.yarn_issue_slip_detail import YarnIssueSlipDetail
from app.schemas.yarn_issue_slip_detail_schema import (
    YarnIssueSlipDetailCreate,
    YarnIssueSlipDetailUpdate
)


# =========================
# GET LIST (KHÔNG SEARCH)
# =========================
def get_issue_details(
    db: Session,
    skip: int = 0,
    limit: int = 100
):
    return (
        db.query(YarnIssueSlipDetail)
        .offset(skip)
        .limit(limit)
        .all()
    )


# =========================
# SEARCH (PHIẾU / SỢI / MÁY)
# =========================
def search_issue_details(
    db: Session,
    issue_slip_id: int | None = None,
    yarn_id: int | None = None,
    machine_id: int | None = None,
    skip: int = 0,
    limit: int = 100
):
    query = db.query(YarnIssueSlipDetail)

    if issue_slip_id:
        query = query.filter(
            YarnIssueSlipDetail.issue_slip_id == issue_slip_id
        )

    if yarn_id:
        query = query.filter(
            YarnIssueSlipDetail.yarn_id == yarn_id
        )

    if machine_id:
        query = query.filter(
            YarnIssueSlipDetail.machine_id == machine_id
        )

    return (
        query
        .offset(skip)
        .limit(limit)
        .all()
    )


# =========================
# CREATE
# =========================
def create_issue_detail(
    db: Session,
    data: YarnIssueSlipDetailCreate
):
    detail = YarnIssueSlipDetail(**data.model_dump())
    db.add(detail)
    db.commit()
    db.refresh(detail)
    return detail


# =========================
# UPDATE
# =========================
def update_issue_detail(
    db: Session,
    issue_detail_id: int,
    data: YarnIssueSlipDetailUpdate
):
    detail = db.get(YarnIssueSlipDetail, issue_detail_id)
    if not detail:
        return None

    update_data = data.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(detail, k, v)

    db.commit()
    db.refresh(detail)
    return detail


# =========================
# DELETE
# =========================
def delete_issue_detail(
    db: Session,
    issue_detail_id: int
):
    detail = db.get(YarnIssueSlipDetail, issue_detail_id)
    if not detail:
        return False

    db.delete(detail)
    db.commit()
    return True
