from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional

from app.api import deps
from app.core.websockets import ws_manager

from app.schemas.material_type_schema import MaterialTypeCreate, MaterialTypeUpdate, MaterialTypeResponse
from app.services import material_type_service

router = APIRouter()

@router.get("/count", response_model=int)
def get_type_count(db: Session = Depends(deps.get_db)):
    """Lấy tổng số lượng Loại NVL"""
    return material_type_service.count_types(db)

@router.get("/", response_model=List[MaterialTypeResponse])
def read_types(
    skip: int = 0, 
    limit: int = 100, 
    search: Optional[str] = None, 
    db: Session = Depends(deps.get_db)
):
    """Lấy danh sách Loại NVL"""
    return material_type_service.get_types(db, skip=skip, limit=limit, search=search)

@router.get("/{type_id}", response_model=MaterialTypeResponse)
def read_type(type_id: int, db: Session = Depends(deps.get_db)):
    """Lấy chi tiết 1 Loại NVL"""
    type_obj = material_type_service.get_type_by_id(db, type_id)
    if not type_obj:
        raise HTTPException(status_code=404, detail="Không tìm thấy Loại NVL.")
    return type_obj

@router.post("/", response_model=MaterialTypeResponse)
def create_type(
    type_in: MaterialTypeCreate, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db)
):
    """Thêm mới Loại NVL"""
    new_type = material_type_service.create_type(db, type_in)
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_MATERIAL_TYPES")
    return new_type

@router.put("/{type_id}", response_model=MaterialTypeResponse)
def update_type(
    type_id: int, 
    type_in: MaterialTypeUpdate, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db)
):
    """Cập nhật Loại NVL"""
    updated_type = material_type_service.update_type(db, type_id, type_in)
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_MATERIAL_TYPES")
    return updated_type

@router.delete("/{type_id}")
def delete_type(
    type_id: int, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db)
):
    """Xóa Loại NVL"""
    result = material_type_service.delete_type(db, type_id)
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_MATERIAL_TYPES")
    return result