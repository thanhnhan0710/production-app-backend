# [THÊM] Import BackgroundTasks
from fastapi import APIRouter, Depends, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional

from app.api import deps
from app.schemas.warehouse_schema import WarehouseCreate, WarehouseUpdate, WarehouseResponse
from app.services.warehouse_service import WarehouseService

# --- [THÊM] Import ws_manager để gọi WebSocket ---
from app.core.websockets import ws_manager

router = APIRouter()

# =========================
# GET LIST (Không cần WebSocket)
# =========================
@router.get("/", response_model=List[WarehouseResponse])
def read_warehouses(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = Query(None, description="Tìm theo tên kho hoặc vị trí"),
    db: Session = Depends(deps.get_db)
):
    service = WarehouseService(db)
    return service.get_multi(skip=skip, limit=limit, search=search)

# =========================
# CREATE
# =========================
@router.post("/", response_model=WarehouseResponse)
def create_warehouse(
    warehouse_in: WarehouseCreate, 
    background_tasks: BackgroundTasks, # [THÊM] BackgroundTasks
    db: Session = Depends(deps.get_db)
):
    service = WarehouseService(db)
    new_warehouse = service.create(obj_in=warehouse_in)
    
    # [THÊM] Bắn tín hiệu yêu cầu Client tải lại danh sách Kho
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_WAREHOUSES")
    
    return new_warehouse

# =========================
# UPDATE
# =========================
@router.put("/{warehouse_id}", response_model=WarehouseResponse)
def update_warehouse(
    warehouse_id: int, 
    warehouse_in: WarehouseUpdate, 
    background_tasks: BackgroundTasks, # [THÊM] BackgroundTasks
    db: Session = Depends(deps.get_db)
):
    service = WarehouseService(db)
    updated_warehouse = service.update(warehouse_id=warehouse_id, obj_in=warehouse_in)
    
    # [THÊM] Bắn tín hiệu WebSocket
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_WAREHOUSES")
    
    return updated_warehouse

# =========================
# DELETE
# =========================
@router.delete("/{warehouse_id}")
def delete_warehouse(
    warehouse_id: int, 
    background_tasks: BackgroundTasks, # [THÊM] BackgroundTasks
    db: Session = Depends(deps.get_db)
):
    service = WarehouseService(db)
    result = service.delete(warehouse_id=warehouse_id)
    
    # [THÊM] Bắn tín hiệu WebSocket
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_WAREHOUSES")
    
    return result