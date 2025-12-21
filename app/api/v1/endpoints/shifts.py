from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.api import deps
from app.schemas.shift_schema import (
    ShiftResponse,
    ShiftCreate,
    ShiftUpdate
)
from app.services import shift_service

router = APIRouter()


# =========================
# GET LIST
# =========================
@router.get("/", response_model=List[ShiftResponse])
def read_shifts(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db)
):
    return shift_service.get_shifts(db, skip, limit)


# =========================
# CREATE
# =========================
@router.post("/", response_model=ShiftResponse)
def create_shift(
    shift: ShiftCreate,
    db: Session = Depends(deps.get_db)
):
    return shift_service.create_shift(db, shift)


# =========================
# UPDATE
# =========================
@router.put("/{shift_id}", response_model=ShiftResponse)
def update_shift(
    shift_id: int,
    shift: ShiftUpdate,
    db: Session = Depends(deps.get_db)
):
    updated_shift = shift_service.update_shift(
        db, shift_id, shift
    )
    if not updated_shift:
        raise HTTPException(status_code=404, detail="Shift not found")
    return updated_shift


# =========================
# DELETE
# =========================
@router.delete("/{shift_id}")
def delete_shift(
    shift_id: int,
    db: Session = Depends(deps.get_db)
):
    success = shift_service.delete_shift(db, shift_id)
    if not success:
        raise HTTPException(status_code=404, detail="Shift not found")
    return {"message": "Deleted successfully"}


# =========================
# SEARCH
# =========================
@router.get("/search", response_model=List[ShiftResponse])
def search_shifts(
    keyword: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db)
):
    return shift_service.search_shifts(
        db, keyword, skip, limit
    )
