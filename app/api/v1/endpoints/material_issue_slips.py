from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from app.api import deps
from app.schemas.material_issue_slip_schema import (
    MaterialIssueSlipResponse,
    MaterialIssueSlipCreate,
    MaterialIssueSlipUpdate
)
from app.services import material_issue_slip_service

router = APIRouter()

@router.get("/", response_model=List[MaterialIssueSlipResponse])
def read_material_issue_slips(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db)
):
    return material_issue_slip_service.get_material_issue_slips(
        db, skip, limit
    )


@router.post("/", response_model=MaterialIssueSlipResponse)
def create_material_issue_slip(
    data: MaterialIssueSlipCreate,
    db: Session = Depends(deps.get_db)
):
    return material_issue_slip_service.create_material_issue_slip(
        db, data
    )

@router.put("/{issue_slip_id}", response_model=MaterialIssueSlipResponse)
def update_material_issue_slip(
    issue_slip_id: int,
    data: MaterialIssueSlipUpdate,
    db: Session = Depends(deps.get_db)
):
    slip = material_issue_slip_service.update_material_issue_slip(
        db, issue_slip_id, data
    )
    if not slip:
        raise HTTPException(
            status_code=404,
            detail="Material issue slip not found"
        )
    return slip

@router.delete("/{issue_slip_id}")
def delete_material_issue_slip(
    issue_slip_id: int,
    db: Session = Depends(deps.get_db)
):
    success = material_issue_slip_service.delete_material_issue_slip(
        db, issue_slip_id
    )
    if not success:
        raise HTTPException(
            status_code=404,
            detail="Material issue slip not found"
        )
    return {"message": "Deleted successfully"}

@router.get("/search", response_model=List[MaterialIssueSlipResponse])
def search_material_issue_slips(
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    employee_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db)
):
    return material_issue_slip_service.search_material_issue_slips(
        db=db,
        from_date=from_date,
        to_date=to_date,
        employee_id=employee_id,
        skip=skip,
        limit=limit
    )
