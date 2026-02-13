from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks # [THÊM] BackgroundTasks
from sqlalchemy.orm import Session
from typing import List

from app.api import deps
# Import schemas đã định nghĩa
from app.schemas.material_schema import (
    MaterialResponse,
    MaterialCreate,
    MaterialUpdate
)
# Import service đã định nghĩa
from app.services import material_service

# --- [THÊM] Import ws_manager để gọi WebSocket ---
from app.core.websockets import ws_manager

router = APIRouter()

# =========================
# GET LIST (Danh sách)
# =========================
@router.get("/", response_model=List[MaterialResponse])
def read_materials(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db)
):
    """
    Lấy danh sách vật tư.
    """
    return material_service.get_materials(db, skip, limit)


# =========================
# SEARCH (Tìm kiếm)
# =========================
@router.get("/search", response_model=List[MaterialResponse])
def search_materials(
    keyword: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db)
):
    """
    Tìm kiếm vật tư theo Mã, Tên, Loại, Denier, HS Code.
    """
    return material_service.search_materials(
        db, keyword, skip, limit
    )


# =========================
# CREATE (Thêm mới)
# =========================
@router.post("/", response_model=MaterialResponse, status_code=status.HTTP_201_CREATED)
def create_material(
    material_in: MaterialCreate,
    background_tasks: BackgroundTasks, # [THÊM] BackgroundTasks
    db: Session = Depends(deps.get_db)
):
    """
    Tạo mới một vật tư.
    Có kiểm tra trùng mã (material_code).
    """
    # 1. Kiểm tra mã đã tồn tại chưa
    existing_material = material_service.get_material_by_code(db, material_code=material_in.material_code)
    if existing_material:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Mã vật tư '{material_in.material_code}' đã tồn tại trong hệ thống."
        )

    # 2. Tạo mới nếu mã hợp lệ
    new_material = material_service.create_material(db, material_in)
    
    # [THÊM] Bắn tín hiệu WebSocket để các màn hình Danh mục vật tư tải lại dữ liệu
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_MATERIALS")
    
    return new_material


# =========================
# UPDATE (Cập nhật)
# =========================
@router.put("/{material_id}", response_model=MaterialResponse)
def update_material(
    material_id: int,
    material_in: MaterialUpdate,
    background_tasks: BackgroundTasks, # [THÊM] BackgroundTasks
    db: Session = Depends(deps.get_db)
):
    """
    Cập nhật thông tin vật tư theo ID.
    """
    updated_material = material_service.update_material(
        db, material_id, material_in
    )
    
    if not updated_material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Material not found"
        )
    
    # [THÊM] Bắn tín hiệu WebSocket
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_MATERIALS")
        
    return updated_material


# =========================
# DELETE (Xóa)
# =========================
@router.delete("/{material_id}")
def delete_material(
    material_id: int,
    background_tasks: BackgroundTasks, # [THÊM] BackgroundTasks
    db: Session = Depends(deps.get_db)
):
    """
    Xóa vật tư theo ID.
    """
    success = material_service.delete_material(db, material_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Material not found"
        )
    
    # [THÊM] Bắn tín hiệu WebSocket
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_MATERIALS")
        
    return {"message": "Deleted successfully"}