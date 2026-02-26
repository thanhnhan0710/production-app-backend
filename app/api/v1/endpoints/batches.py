from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks # [MỚI] Thêm BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional

from app.api import deps
from app.schemas.batch_schema import BatchResponse, BatchCreate, BatchUpdate, BatchQCStatus
from app.services.batch_service import BatchService
from app.core.websockets import ws_manager # [MỚI] Thêm WebSocket Manager

router = APIRouter()

# 1. Lấy danh sách (Có bổ sung filter receipt_detail_id)
@router.get("/", response_model=List[BatchResponse])
def read_batches(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    supplier_batch: Optional[str] = None,
    material_id: Optional[int] = None,
    qc_status: Optional[BatchQCStatus] = None,
    db: Session = Depends(deps.get_db)
):
    service = BatchService(db)
    return service.get_multi(
        skip=skip, 
        limit=limit, 
        search=search, 
        material_id=material_id, 
        qc_status=qc_status, 
        supplier_batch=supplier_batch
    )

# 2. Tạo mới (Có WebSocket)
@router.post("/", response_model=BatchResponse)
def create_batch(
    batch_in: BatchCreate, 
    background_tasks: BackgroundTasks, # [MỚI]
    db: Session = Depends(deps.get_db)
):
    service = BatchService(db)
    new_batch = service.create(batch_in)
    
    # [MỚI] Bắn tín hiệu WebSocket
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_BATCHES")
    return new_batch

# 3. Xem chi tiết
@router.get("/{batch_id}", response_model=BatchResponse)
def read_batch(batch_id: int, db: Session = Depends(deps.get_db)):
    service = BatchService(db)
    batch = service.get(batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Không tìm thấy lô hàng")
    return batch

# 4. Cập nhật (Có WebSocket)
@router.put("/{batch_id}", response_model=BatchResponse)
def update_batch(
    batch_id: int, 
    batch_in: BatchUpdate, 
    background_tasks: BackgroundTasks, # [MỚI]
    db: Session = Depends(deps.get_db)
):
    service = BatchService(db)
    batch = service.get(batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Không tìm thấy lô hàng")
        
    updated_batch = service.update(db_obj=batch, obj_in=batch_in)
    
    # [MỚI] Bắn tín hiệu WebSocket
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_BATCHES")
    return updated_batch

# 5. Cập nhật trạng thái QC (Có WebSocket)
@router.put("/{batch_id}/qc-status", response_model=BatchResponse)
def update_batch_qc_status(
    batch_id: int, 
    status: BatchQCStatus, 
    background_tasks: BackgroundTasks, # [MỚI]
    note: Optional[str] = None,
    db: Session = Depends(deps.get_db)
):
    service = BatchService(db)
    updated_batch = service.update_qc_status(batch_id=batch_id, status=status, note=note)
    
    # [MỚI] Bắn tín hiệu WebSocket
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_BATCHES")
    return updated_batch

# 6. Xóa (Có WebSocket)
@router.delete("/{batch_id}")
def delete_batch(
    batch_id: int, 
    background_tasks: BackgroundTasks, # [MỚI]
    db: Session = Depends(deps.get_db)
):
    service = BatchService(db)
    service.delete(batch_id)
    
    # [MỚI] Bắn tín hiệu WebSocket
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_BATCHES")
    return {"message": "Xóa lô hàng thành công"}