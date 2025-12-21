from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from app.api import deps
from app.schemas.material_issue_slip_detail_schema import (
    MaterialIssueSlipDetailResponse,
    MaterialIssueSlipDetailCreate,
    MaterialIssueSlipDetailUpdate
)
from app.services import material_issue_slip_detail_service

router = APIRouter()

@router.get("/", response_model=List[MaterialIssueSlipDetailResponse])
def read_material_issue_details(
    issue_slip_id: Optional[int] = None,
    material_id: Optional[int] = None,
    employee_id: Optional[int] = None,
    shift_id: Optional[int] = None,
    db: Session = Depends(deps.get_db)
):
    return material_issue_slip_detail_service.get_material_issue_details(
        db,
        issue_slip_id=issue_slip_id,
        material_id=material_id,
        employee_id=employee_id,
        shift_id=shift_id
    )

@router.post("/", response_model=MaterialIssueSlipDetailResponse)
def create_material_issue_detail(
    data: MaterialIssueSlipDetailCreate,
    db: Session = Depends(deps.get_db)
):
    return material_issue_slip_detail_service.create_material_issue_detail(
        db, data
    )


@router.put("/{issue_detail_id}", response_model=MaterialIssueSlipDetailResponse)
def update_material_issue_detail(
    issue_detail_id: int,
    data: MaterialIssueSlipDetailUpdate,
    db: Session = Depends(deps.get_db)
):
    detail = material_issue_slip_detail_service.update_material_issue_detail(
        db, issue_detail_id, data
    )
    if not detail:
        raise HTTPException(
            status_code=404,
            detail="Material issue slip detail not found"
        )
    return detail

@router.delete("/{issue_detail_id}")
def delete_material_issue_detail(
    issue_detail_id: int,
    db: Session = Depends(deps.get_db)
):
    success = material_issue_slip_detail_service.delete_material_issue_detail(
        db, issue_detail_id
    )
    if not success:
        raise HTTPException(
            status_code=404,
            detail="Material issue slip detail not found"
        )
    return {"message": "Deleted successfully"}
