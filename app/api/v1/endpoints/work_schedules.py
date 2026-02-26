from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from app.api import deps
from app.schemas.work_schedule_schema import WorkScheduleResponse, WorkScheduleCreate, WorkScheduleUpdate
from app.services import work_schedule_service
from app.core.websockets import ws_manager # Import WebSocket Manager

# DÒNG NÀY RẤT QUAN TRỌNG ĐỂ FIX LỖI BẠN ĐANG GẶP
router = APIRouter()

# =========================
# GET LIST
# =========================
@router.get("/", response_model=List[WorkScheduleResponse])
def read_schedules(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(deps.get_db)
):
    return work_schedule_service.get_schedules(db, skip=skip, limit=limit)

# =========================
# SEARCH
# =========================
@router.get("/search", response_model=List[WorkScheduleResponse])
def search_schedules(
    employee_id: Optional[int] = None,
    shift_id: Optional[int] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db)
):
    return work_schedule_service.search_schedules(
        db, 
        employee_id=employee_id, 
        shift_id=shift_id, 
        from_date=from_date, 
        to_date=to_date, 
        skip=skip, 
        limit=limit
    )

# =========================
# CREATE
# =========================
@router.post("/", response_model=WorkScheduleResponse)
def create_schedule(
    schedule_in: WorkScheduleCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db)
):
    new_schedule = work_schedule_service.create_schedule(db, schedule_in)
    
    # Bắn WebSocket sau khi tạo
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_WORK_SCHEDULES")
    return new_schedule

# =========================
# UPDATE
# =========================
@router.put("/{schedule_id}", response_model=WorkScheduleResponse)
def update_schedule(
    schedule_id: int,
    schedule_in: WorkScheduleUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db)
):
    updated_schedule = work_schedule_service.update_schedule(db, schedule_id, schedule_in)
    
    # Bắn WebSocket sau khi sửa
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_WORK_SCHEDULES")
    return updated_schedule

# =========================
# DELETE
# =========================
@router.delete("/{schedule_id}")
def delete_schedule(
    schedule_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db)
):
    result = work_schedule_service.delete_schedule(db, schedule_id)
    
    # Bắn WebSocket sau khi xóa
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_WORK_SCHEDULES")
    return result