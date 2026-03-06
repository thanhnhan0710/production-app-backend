from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.api import deps
from app.core.websockets import ws_manager
from app.schemas.incoterm_schema import IncotermCreate, IncotermUpdate, IncotermResponse
from app.services import incoterm_service

router = APIRouter()

@router.get("/", response_model=List[IncotermResponse])
def read_incoterms(
    search: Optional[str] = Query(None, description="Tìm theo mã hoặc mô tả"),
    db: Session = Depends(deps.get_db)
):
    """Lấy danh sách tất cả các điều kiện giao hàng (Incoterm)"""
    return incoterm_service.get_incoterms(db, search=search)

@router.post("/", response_model=IncotermResponse, status_code=status.HTTP_201_CREATED)
def create_incoterm(
    incoterm_in: IncotermCreate, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db)
):
    """Tạo mới một điều kiện giao hàng"""
    new_incoterm = incoterm_service.create_incoterm(db=db, incoterm_in=incoterm_in)
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_INCOTERMS")
    return new_incoterm

@router.put("/{incoterm_id}", response_model=IncotermResponse)
def update_incoterm(
    incoterm_id: int, 
    incoterm_in: IncotermUpdate, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db)
):
    """Cập nhật thông tin điều kiện giao hàng"""
    updated_incoterm = incoterm_service.update_incoterm(db=db, incoterm_id=incoterm_id, incoterm_in=incoterm_in)
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_INCOTERMS")
    return updated_incoterm

@router.delete("/{incoterm_id}")
def delete_incoterm(
    incoterm_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db)
):
    """Xóa một điều kiện giao hàng"""
    result = incoterm_service.delete_incoterm(db=db, incoterm_id=incoterm_id)
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_INCOTERMS")
    return result