from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.api import deps
from app.schemas.yarn_issue_slip_detail_schema import (
    YarnIssueSlipDetailResponse,
    YarnIssueSlipDetailCreate,
    YarnIssueSlipDetailUpdate
)
from app.services import yarn_issue_slip_detail_service

router = APIRouter()


# =========================
# GET LIST
# =========================
@router.get("/", response_model=List[YarnIssueSlipDetailResponse])
def read_issue_details(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db)
):
    return yarn_issue_slip_detail_service.get_issue_details(
        db, skip, limit
    )


# =========================
# SEARCH
# =========================
@router.get("/search", response_model=List[YarnIssueSlipDetailResponse])
def search_issue_details(
    issue_slip_id: int | None = None,
    yarn_id: int | None = None,
    machine_id: int | None = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db)
):
    return yarn_issue_slip_detail_service.search_issue_details(
        db=db,
        issue_slip_id=issue_slip_id,
        yarn_id=yarn_id,
        machine_id=machine_id,
        skip=skip,
        limit=limit
    )


# =========================
# CREATE
# =========================
@router.post("/", response_model=YarnIssueSlipDetailResponse)
def create_issue_detail(
    detail: YarnIssueSlipDetailCreate,
    db: Session = Depends(deps.get_db)
):
    return yarn_issue_slip_detail_service.create_issue_detail(
        db, detail
    )


# =========================
# UPDATE
# =========================
@router.put("/{issue_detail_id}", response_model=YarnIssueSlipDetailResponse)
def update_issue_detail(
    issue_detail_id: int,
    detail: YarnIssueSlipDetailUpdate,
    db: Session = Depends(deps.get_db)
):
    updated_detail = yarn_issue_slip_detail_service.update_issue_detail(
        db, issue_detail_id, detail
    )
    if not updated_detail:
        raise HTTPException(
            status_code=404,
            detail="Issue slip detail not found"
        )
    return updated_detail


# =========================
# DELETE
# =========================
@router.delete("/{issue_detail_id}")
def delete_issue_detail(
    issue_detail_id: int,
    db: Session = Depends(deps.get_db)
):
    success = yarn_issue_slip_detail_service.delete_issue_detail(
        db, issue_detail_id
    )
    if not success:
        raise HTTPException(
            status_code=404,
            detail="Issue slip detail not found"
        )
    return {"message": "Deleted successfully"}
