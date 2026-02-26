from fastapi import APIRouter, Depends, Query, HTTPException, BackgroundTasks # [MỚI] Thêm BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from datetime import date

from app.api import deps
from app.schemas.material_export_schema import (
    MaterialExportCreate, 
    MaterialExportUpdate, 
    MaterialExportResponse,
    MaterialExportFilter
)
from app.services.material_export_service import MaterialExportService
from app.core.websockets import ws_manager # [MỚI] Import WebSocket Manager

router = APIRouter()

# Endpoint lấy số phiếu xuất tự động
@router.get("/next-number", response_model=Dict[str, str])
def get_next_export_number(db: Session = Depends(deps.get_db)):
    """
    Sinh mã phiếu xuất tiếp theo: YYYYMM-XXXX (VD: 202601-0001).
    """
    service = MaterialExportService(db)
    new_code = service.generate_next_export_code()
    return {"export_code": new_code}

@router.get("/", response_model=List[MaterialExportResponse])
def read_exports(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    warehouse_id: Optional[int] = None,
    exporter_id: Optional[int] = None,
    receiver_id: Optional[int] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    db: Session = Depends(deps.get_db)
):
    service = MaterialExportService(db)
    filters = MaterialExportFilter(
        search=search,
        warehouse_id=warehouse_id,
        exporter_id=exporter_id,
        receiver_id=receiver_id,
        from_date=from_date,
        to_date=to_date
    )
    return service.get_multi(skip=skip, limit=limit, filter_param=filters)

@router.post("/", response_model=MaterialExportResponse)
def create_export(
    export_in: MaterialExportCreate, 
    background_tasks: BackgroundTasks, # [MỚI] Thêm BackgroundTasks
    db: Session = Depends(deps.get_db)
):
    service = MaterialExportService(db)
    new_export = service.create_export(export_in)
    
    # [MỚI] Bắn tín hiệu làm mới danh sách phiếu xuất và tồn kho
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_MATERIAL_EXPORTS")
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_INVENTORY") # Xuất kho thì tồn kho sẽ đổi
    return new_export

@router.get("/{id}", response_model=MaterialExportResponse)
def read_export_detail(id: int, db: Session = Depends(deps.get_db)):
    service = MaterialExportService(db)
    item = service.get(id)
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    return item

@router.put("/{id}", response_model=MaterialExportResponse)
def update_export(
    id: int, 
    export_in: MaterialExportUpdate, 
    background_tasks: BackgroundTasks, # [MỚI] Thêm BackgroundTasks
    db: Session = Depends(deps.get_db)
):
    service = MaterialExportService(db)
    updated_export = service.update(id, export_in)
    
    # [MỚI] Bắn tín hiệu làm mới danh sách phiếu xuất và tồn kho
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_MATERIAL_EXPORTS")
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_INVENTORY")
    return updated_export

@router.delete("/{id}")
def delete_export(
    id: int, 
    background_tasks: BackgroundTasks, # [MỚI] Thêm BackgroundTasks
    db: Session = Depends(deps.get_db)
):
    service = MaterialExportService(db)
    result = service.delete(id)
    
    # [MỚI] Bắn tín hiệu làm mới danh sách phiếu xuất và tồn kho
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_MATERIAL_EXPORTS")
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_INVENTORY")
    return result