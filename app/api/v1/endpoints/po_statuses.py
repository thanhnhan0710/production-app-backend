from fastapi import APIRouter, Depends, status, BackgroundTasks, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.api import deps
from app.core.websockets import ws_manager
from app.schemas.po_status_schema import POStatusCreate, POStatusUpdate, POStatusResponse
from app.services import po_status_service

router = APIRouter()

@router.get("/", response_model=List[POStatusResponse])
def read_po_statuses(
    search: Optional[str] = Query(None, description="Tìm theo mã hoặc mô tả"),
    db: Session = Depends(deps.get_db)
):
    """Lấy danh sách tất cả trạng thái đơn hàng"""
    return po_status_service.get_po_statuses(db, search=search)

@router.post("/", response_model=POStatusResponse, status_code=status.HTTP_201_CREATED)
def create_po_status(
    status_in: POStatusCreate, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db)
):
    """Tạo mới một trạng thái đơn hàng"""
    new_status = po_status_service.create_po_status(db=db, status_in=status_in)
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_PO_STATUSES")
    return new_status

@router.put("/{status_id}", response_model=POStatusResponse)
def update_po_status(
    status_id: int, 
    status_in: POStatusUpdate, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db)
):
    """Cập nhật thông tin trạng thái đơn hàng"""
    updated_status = po_status_service.update_po_status(db=db, status_id=status_id, status_in=status_in)
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_PO_STATUSES")
    return updated_status

@router.delete("/{status_id}")
def delete_po_status(
    status_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db)
):
    """Xóa một trạng thái đơn hàng"""
    result = po_status_service.delete_po_status(db=db, status_id=status_id)
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_PO_STATUSES")
    return result