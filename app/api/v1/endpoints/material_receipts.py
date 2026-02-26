from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks # [MỚI] Thêm BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from datetime import date

from app.api import deps
from app.schemas.material_receipt_schema import (
    MaterialReceiptCreate, 
    MaterialReceiptUpdate, 
    MaterialReceiptResponse,
    MaterialReceiptDetailCreate,
    MaterialReceiptDetailUpdate,
    MaterialReceiptDetailResponse,
    MaterialReceiptFilter
)
from app.services.material_receipt_service import MaterialReceiptService
from app.core.websockets import ws_manager # [MỚI] Thêm WebSocket Manager

router = APIRouter()

# --- HEADER ENDPOINTS ---

@router.get("/next-number", response_model=Dict[str, str])
def get_next_number(db: Session = Depends(deps.get_db)):
    """
    Sinh số phiếu nhập tiếp theo: YYYY/MM-XXX.
    """
    service = MaterialReceiptService(db)
    new_number = service.generate_next_receipt_number()
    return {"receipt_number": new_number}

@router.get("/", response_model=List[MaterialReceiptResponse])
def read_receipts(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = Query(None),
    po_id: Optional[int] = Query(None),
    declaration_id: Optional[int] = Query(None),
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    db: Session = Depends(deps.get_db)
):
    service = MaterialReceiptService(db)
    filter_params = MaterialReceiptFilter(
        search=search,
        po_id=po_id,
        declaration_id=declaration_id,
        from_date=from_date,
        to_date=to_date
    )
    return service.get_multi(skip=skip, limit=limit, filter_param=filter_params)

@router.post("/", response_model=MaterialReceiptResponse)
def create_receipt(
    receipt_in: MaterialReceiptCreate, 
    background_tasks: BackgroundTasks, # [MỚI]
    db: Session = Depends(deps.get_db)
):
    service = MaterialReceiptService(db)
    new_receipt = service.create(obj_in=receipt_in)
    
    # [MỚI] Bắn tín hiệu WebSocket
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_MATERIAL_RECEIPTS")
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_INVENTORY") # Ảnh hưởng tồn kho
    return new_receipt

@router.get("/{receipt_id}", response_model=MaterialReceiptResponse)
def read_receipt(
    receipt_id: int, 
    db: Session = Depends(deps.get_db)
):
    service = MaterialReceiptService(db)
    item = service.get(receipt_id)
    if not item:
        raise HTTPException(status_code=404, detail="Phiếu nhập không tồn tại.")
    return item

@router.put("/{receipt_id}", response_model=MaterialReceiptResponse)
def update_receipt(
    receipt_id: int, 
    receipt_in: MaterialReceiptUpdate, 
    background_tasks: BackgroundTasks, # [MỚI]
    db: Session = Depends(deps.get_db)
):
    service = MaterialReceiptService(db)
    updated_receipt = service.update(receipt_id, obj_in=receipt_in)
    
    # [MỚI] Bắn tín hiệu WebSocket
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_MATERIAL_RECEIPTS")
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_INVENTORY")
    return updated_receipt

@router.delete("/{receipt_id}")
def delete_receipt(
    receipt_id: int, 
    background_tasks: BackgroundTasks, # [MỚI]
    db: Session = Depends(deps.get_db)
):
    service = MaterialReceiptService(db)
    result = service.delete(receipt_id)
    
    # [MỚI] Bắn tín hiệu WebSocket
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_MATERIAL_RECEIPTS")
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_INVENTORY")
    return result

# --- DETAIL ENDPOINTS ---

@router.post("/{receipt_id}/details", response_model=MaterialReceiptDetailResponse)
def add_receipt_detail(
    receipt_id: int, 
    detail_in: MaterialReceiptDetailCreate, 
    background_tasks: BackgroundTasks, # [MỚI]
    db: Session = Depends(deps.get_db)
):
    service = MaterialReceiptService(db)
    new_detail = service.add_detail(receipt_id=receipt_id, detail_in=detail_in)
    
    # [MỚI] Bắn tín hiệu WebSocket
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_MATERIAL_RECEIPTS")
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_INVENTORY")
    return new_detail

@router.put("/details/{detail_id}", response_model=MaterialReceiptDetailResponse)
def update_receipt_detail(
    detail_id: int, 
    detail_in: MaterialReceiptDetailUpdate, 
    background_tasks: BackgroundTasks, # [MỚI]
    db: Session = Depends(deps.get_db)
):
    service = MaterialReceiptService(db)
    updated_detail = service.update_detail(detail_id=detail_id, obj_in=detail_in)
    
    # [MỚI] Bắn tín hiệu WebSocket
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_MATERIAL_RECEIPTS")
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_INVENTORY")
    return updated_detail

@router.delete("/details/{detail_id}")
def delete_receipt_detail(
    detail_id: int, 
    background_tasks: BackgroundTasks, # [MỚI]
    db: Session = Depends(deps.get_db)
):
    service = MaterialReceiptService(db)
    result = service.delete_detail(detail_id=detail_id)
    
    # [MỚI] Bắn tín hiệu WebSocket
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_MATERIAL_RECEIPTS")
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_INVENTORY")
    return result