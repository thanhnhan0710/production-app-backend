from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from app.api import deps
from app.schemas.work_schedule_schema import (
    WorkScheduleResponse,
    WorkScheduleCreate,
    WorkScheduleUpdate
)
from app.services import work_schedule_service

router = APIRouter()

# =========================
# GET LIST (Default)
# =========================
@router.get("/", response_model=List[WorkScheduleResponse])
def read_work_schedules(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db)
):
    """
    Get list of work schedules (sorted by date descending).
    """
    return work_schedule_service.get_schedules(db, skip, limit)


# =========================
# SEARCH (Advanced Filter)
# =========================
@router.get("/search", response_model=List[WorkScheduleResponse])
def search_work_schedules(
    employee_id: Optional[int] = None,
    shift_id: Optional[int] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db)
):
    """
    Search schedules by Employee, Shift, or Date Range.
    Example: Find schedule of Employee 1 in December 2023.
    """
    return work_schedule_service.search_schedules(
        db=db,
        employee_id=employee_id,
        shift_id=shift_id,
        from_date=from_date,
        to_date=to_date,
        skip=skip,
        limit=limit
    )


# =========================
# GET DETAIL
# =========================
@router.get("/{schedule_id}", response_model=WorkScheduleResponse)
def read_work_schedule(
    schedule_id: int,
    db: Session = Depends(deps.get_db)
):
    """
    Get specific schedule details by ID.
    """
    schedule = work_schedule_service.get_schedule_by_id(db, schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="Work schedule not found")
    return schedule


# =========================
# CREATE
# =========================
@router.post("/", response_model=WorkScheduleResponse)
def create_work_schedule(
    schedule_in: WorkScheduleCreate,
    db: Session = Depends(deps.get_db)
):
    """
    Create a new schedule.
    Validation: Prevents double-booking (same employee, same date).
    """
    return work_schedule_service.create_schedule(db, schedule_in)


# =========================
# UPDATE
# =========================
@router.put("/{schedule_id}", response_model=WorkScheduleResponse)
def update_work_schedule(
    schedule_id: int,
    schedule_in: WorkScheduleUpdate,
    db: Session = Depends(deps.get_db)
):
    """
    Update schedule info (change date, shift, or employee).
    Validation: Checks for conflicts if date/employee changes.
    """
    return work_schedule_service.update_schedule(db, schedule_id, schedule_in)


# =========================
# DELETE
# =========================
@router.delete("/{schedule_id}")
def delete_work_schedule(
    schedule_id: int,
    db: Session = Depends(deps.get_db)
):
    """
    Delete a schedule.
    """
    return work_schedule_service.delete_schedule(db, schedule_id)