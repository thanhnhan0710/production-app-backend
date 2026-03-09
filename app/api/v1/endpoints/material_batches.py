from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional

from app.api import deps
from app.core.websockets import ws_manager

from app.schemas.material_batch_schema import MaterialBatchCreate, MaterialBatchUpdate, MaterialBatchResponse
from app.services.material_batch_service import material_batch_service

router = APIRouter()

@router.get("/count", response_model=int)
def get_batch_count(db: Session = Depends(deps.get_db)):
    """Lấy tổng số lượng Lô nguyên vật liệu"""
    return material_batch_service.count_batches(db)

@router.get("/", response_model=List[MaterialBatchResponse])
def read_batches(
    skip: int = 0, 
    limit: int = 100, 
    search: Optional[str] = None,
    material_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(deps.get_db)
):
    """Lấy danh sách Lô nguyên vật liệu"""
    return material_batch_service.get_batches(
        db, skip=skip, limit=limit, search=search, material_id=material_id, status=status
    )

@router.get("/{batch_id}", response_model=MaterialBatchResponse)
def read_batch(batch_id: int, db: Session = Depends(deps.get_db)):
    """Lấy chi tiết 1 Lô nguyên vật liệu theo ID"""
    batch = material_batch_service.get_batch(db, batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Không tìm thấy Lô nguyên vật liệu.")
    return batch

@router.get("/code/{batch_code}", response_model=MaterialBatchResponse)
def read_batch_by_code(batch_code: str, db: Session = Depends(deps.get_db)):
    """Lấy chi tiết 1 Lô nguyên vật liệu bằng Mã Lô (VD: V260001)"""
    batch = material_batch_service.get_batch_by_code(db, batch_code)
    if not batch:
        raise HTTPException(status_code=404, detail="Không tìm thấy Mã Lô này.")
    return batch

@router.post("/", response_model=MaterialBatchResponse)
def create_batch(
    batch_in: MaterialBatchCreate, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db)
):
    """Thêm mới Lô nguyên vật liệu (Thường do hệ thống tự sinh qua API Nhập kho)"""
    new_batch = material_batch_service.create_batch(db, batch_in)
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_MATERIAL_BATCHES")
    return new_batch

@router.put("/{batch_id}", response_model=MaterialBatchResponse)
def update_batch(
    batch_id: int, 
    batch_in: MaterialBatchUpdate, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db)
):
    """Cập nhật trạng thái/thông tin Lô nguyên vật liệu"""
    updated_batch = material_batch_service.update_batch(db, batch_id, batch_in)
    if not updated_batch:
        raise HTTPException(status_code=404, detail="Không tìm thấy Lô để cập nhật.")
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_MATERIAL_BATCHES")
    return updated_batch

@router.delete("/{batch_id}")
def delete_batch(
    batch_id: int, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db)
):
    """Xóa Lô nguyên vật liệu"""
    result = material_batch_service.delete_batch(db, batch_id)
    if not result:
        raise HTTPException(status_code=404, detail="Không tìm thấy Lô nguyên vật liệu.")
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_MATERIAL_BATCHES")
    return {"message": "Đã xóa Lô thành công"}