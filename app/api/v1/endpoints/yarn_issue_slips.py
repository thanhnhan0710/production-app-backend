from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import date

from app.api import deps
from app.schemas.yarn_issue_slip_schema import (
    YarnIssueSlipResponse,
    YarnIssueSlipCreate,
    YarnIssueSlipUpdate
)
from app.services import yarn_issue_slip_service

router = APIRouter()


# =========================
# GET LIST
# =========================
@router.get("/", response_model=List[YarnIssueSlipResponse])
def read_issue_slips(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db)
):
    return yarn_issue_slip_service.get_issue_slips(
        db, skip, limit
    )


# =========================
# CREATE
# =========================
@router.post("/", response_model=YarnIssueSlipResponse)
def create_issue_slip(
    slip: YarnIssueSlipCreate,
    db: Session = Depends(deps.get_db)
):
    return yarn_issue_slip_service.create_issue_slip(db, slip)


# =========================
# UPDATE
# =========================
@router.put("/{issue_slip_id}", response_model=YarnIssueSlipResponse)
def update_issue_slip(
    issue_slip_id: int,
    slip: YarnIssueSlipUpdate,
    db: Session = Depends(deps.get_db)
):
    updated_slip = yarn_issue_slip_service.update_issue_slip(
        db, issue_slip_id, slip
    )
    if not updated_slip:
        raise HTTPException(status_code=404, detail="Issue slip not found")
    return updated_slip


# =========================
# DELETE
# =========================
@router.delete("/{issue_slip_id}")
def delete_issue_slip(
    issue_slip_id: int,
    db: Session = Depends(deps.get_db)
):
    success = yarn_issue_slip_service.delete_issue_slip(
        db, issue_slip_id
    )
    if not success:
        raise HTTPException(status_code=404, detail="Issue slip not found")
    return {"message": "Deleted successfully"}


# =========================
# SEARCH
# =========================
@router.get("/search", response_model=List[YarnIssueSlipResponse])
def search_issue_slips(
    keyword: str | None = None,
    issue_date: date | None = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db)
):
    return yarn_issue_slip_service.search_issue_slips(
        db=db,
        keyword=keyword,
        issue_date=issue_date,
        skip=skip,
        limit=limit
    )
