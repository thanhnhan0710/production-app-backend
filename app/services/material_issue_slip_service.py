from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import date
from typing import Optional

from app.models.material_issue_slip import MaterialIssueSlip
from app.schemas.material_issue_slip_schema import (
    MaterialIssueSlipCreate,
    MaterialIssueSlipUpdate
)

def get_material_issue_slips(
    db: Session,
    skip: int = 0,
    limit: int = 100
):
    return (
        db.query(MaterialIssueSlip)
        .offset(skip)
        .limit(limit)
        .all()
    )

def get_material_issue_slip(
    db: Session,
    issue_slip_id: int
):
    return (
        db.query(MaterialIssueSlip)
        .filter(MaterialIssueSlip.issue_slip_id == issue_slip_id)
        .first()
    )


def create_material_issue_slip(
    db: Session,
    data: MaterialIssueSlipCreate
):
    slip = MaterialIssueSlip(**data.model_dump())
    db.add(slip)
    db.commit()
    db.refresh(slip)
    return slip

def update_material_issue_slip(
    db: Session,
    issue_slip_id: int,
    data: MaterialIssueSlipUpdate
):
    slip = get_material_issue_slip(db, issue_slip_id)
    if not slip:
        return None

    update_data = data.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(slip, k, v)

    db.commit()
    db.refresh(slip)
    return slip

def delete_material_issue_slip(
    db: Session,
    issue_slip_id: int
):
    slip = get_material_issue_slip(db, issue_slip_id)
    if not slip:
        return False

    db.delete(slip)
    db.commit()
    return True

def search_material_issue_slips(
    db: Session,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    employee_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100
):
    query = db.query(MaterialIssueSlip)

    if from_date:
        query = query.filter(MaterialIssueSlip.issue_date >= from_date)

    if to_date:
        query = query.filter(MaterialIssueSlip.issue_date <= to_date)

    if employee_id:
        query = (
            query
            .join(MaterialIssueSlip.details)
            .filter(MaterialIssueSlip.details.any(
                employee_id=employee_id
            ))
        )

    return query.offset(skip).limit(limit).all()
