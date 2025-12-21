from sqlalchemy.orm import Session
from typing import Optional

from app.models.material_issue_slip_detail import MaterialIssueSlipDetail
from app.schemas.material_issue_slip_detail_schema import (
    MaterialIssueSlipDetailCreate,
    MaterialIssueSlipDetailUpdate
)

def get_material_issue_details(
    db: Session,
    issue_slip_id: Optional[int] = None,
    material_id: Optional[int] = None,
    employee_id: Optional[int] = None,
    shift_id: Optional[int] = None
):
    query = db.query(MaterialIssueSlipDetail)

    if issue_slip_id:
        query = query.filter(
            MaterialIssueSlipDetail.issue_slip_id == issue_slip_id
        )

    if material_id:
        query = query.filter(
            MaterialIssueSlipDetail.material_id == material_id
        )

    if employee_id:
        query = query.filter(
            MaterialIssueSlipDetail.employee_id == employee_id
        )

    if shift_id:
        query = query.filter(
            MaterialIssueSlipDetail.shift_id == shift_id
        )

    return query.all()

def create_material_issue_detail(
    db: Session,
    data: MaterialIssueSlipDetailCreate
):
    detail = MaterialIssueSlipDetail(**data.model_dump())
    db.add(detail)
    db.commit()
    db.refresh(detail)
    return detail

def update_material_issue_detail(
    db: Session,
    issue_detail_id: int,
    data: MaterialIssueSlipDetailUpdate
):
    detail = (
        db.query(MaterialIssueSlipDetail)
        .filter(MaterialIssueSlipDetail.issue_detail_id == issue_detail_id)
        .first()
    )
    if not detail:
        return None

    update_data = data.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(detail, k, v)

    db.commit()
    db.refresh(detail)
    return detail

def delete_material_issue_detail(
    db: Session,
    issue_detail_id: int
):
    detail = (
        db.query(MaterialIssueSlipDetail)
        .filter(MaterialIssueSlipDetail.issue_detail_id == issue_detail_id)
        .first()
    )
    if not detail:
        return False

    db.delete(detail)
    db.commit()
    return True
