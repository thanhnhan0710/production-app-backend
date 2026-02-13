from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks # [THÊM] BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional

from app.api import deps
from app.schemas.unit_schema import (
    UnitResponse,
    UnitCreate,
    UnitUpdate
)
from app.services import unit_service

# --- [THÊM] Import ws_manager để gọi WebSocket ---
from app.core.websockets import ws_manager

router = APIRouter()

@router.get("/", response_model=List[UnitResponse])
def read_units(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db)
):
    """
    Lấy danh sách đơn vị tính.
    """
    return unit_service.get_units(db, skip=skip, limit=limit)

@router.post("/", response_model=UnitResponse)
def create_unit(
    data: UnitCreate,
    background_tasks: BackgroundTasks, # [THÊM] BackgroundTasks
    db: Session = Depends(deps.get_db)
):
    """
    Tạo đơn vị tính mới và thông báo qua WebSocket.
    """
    new_unit = unit_service.create_unit(db, data)
    
    # [THÊM] Bắn tín hiệu WebSocket
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_UNITS")
    
    return new_unit

@router.put("/{unit_id}", response_model=UnitResponse)
def update_unit(
    unit_id: int,
    data: UnitUpdate,
    background_tasks: BackgroundTasks, # [THÊM] BackgroundTasks
    db: Session = Depends(deps.get_db)
):
    """
    Cập nhật đơn vị tính và thông báo qua WebSocket.
    """
    unit = unit_service.update_unit(db, unit_id, data)
    if not unit:
        raise HTTPException(
            status_code=404,
            detail="Unit not found"
        )
    
    # [THÊM] Bắn tín hiệu WebSocket
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_UNITS")
    
    return unit


@router.delete("/{unit_id}")
def delete_unit(
    unit_id: int,
    background_tasks: BackgroundTasks, # [THÊM] BackgroundTasks
    db: Session = Depends(deps.get_db)
):
    """
    Xóa đơn vị tính và thông báo qua WebSocket.
    """
    success = unit_service.delete_unit(db, unit_id)
    if not success:
        raise HTTPException(
            status_code=404,
            detail="Unit not found"
        )
    
    # [THÊM] Bắn tín hiệu WebSocket
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_UNITS")
    
    return {"message": "Deleted successfully"}

@router.get("/search", response_model=List[UnitResponse])
def search_units(
    keyword: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db)
):
    """
    Tìm kiếm đơn vị tính.
    """
    return unit_service.search_units(db, keyword, skip, limit)