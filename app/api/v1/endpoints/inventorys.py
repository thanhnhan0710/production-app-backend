from fastapi import APIRouter, Depends, HTTPException, Body, Query, BackgroundTasks # [MỚI] Thêm BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional

from app.api import deps
from app.schemas.inventory_schema import (
    InventoryStockResponse, 
    InventoryAdjustment
)
from app.services.inventory_service import InventoryService
from app.core.websockets import ws_manager # [MỚI] Import WebSocket Manager

router = APIRouter()

# --- 0. GET ALL INVENTORY (LIST) ---
@router.get("/", response_model=List[InventoryStockResponse])
def read_inventories(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = Query(None, description="Tìm theo Material Code/Name hoặc Batch No"),
    warehouse_id: Optional[int] = Query(None, description="Lọc theo ID kho"),
    db: Session = Depends(deps.get_db)
):
    """
    Lấy danh sách tồn kho chi tiết (hỗ trợ phân trang, tìm kiếm, lọc).
    """
    service = InventoryService(db)
    return service.get_multi(
        skip=skip, 
        limit=limit, 
        search=search, 
        warehouse_id=warehouse_id
    )

# --- 1. GET STOCK BY BATCH ---
@router.get("/stock/{warehouse_id}/{batch_id}", response_model=InventoryStockResponse)
def read_stock_by_batch(
    warehouse_id: int,
    batch_id: int,
    db: Session = Depends(deps.get_db)
):
    """
    Get specific stock record for a batch in a warehouse.
    """
    service = InventoryService(db)
    item = service.get_stock_by_batch(warehouse_id, batch_id)
    if not item:
        raise HTTPException(status_code=404, detail="Stock record not found.")
    return item

# --- 2. GET TOTAL STOCK BY MATERIAL ---
@router.get("/material/{material_id}/total", response_model=Dict[str, Any])
def read_total_stock_by_material(
    material_id: int,
    db: Session = Depends(deps.get_db)
):
    """
    Get aggregated stock for a specific material across all warehouses/batches.
    Returns: { "total_on_hand": x, "total_reserved": y, "total_available": z }
    """
    service = InventoryService(db)
    return service.get_total_stock_by_material(material_id)

# --- 3. ADJUST STOCK (STOCK TAKE) ---
@router.post("/adjust", response_model=InventoryStockResponse)
def adjust_stock(
    adjustment: InventoryAdjustment, 
    background_tasks: BackgroundTasks, # [MỚI] Thêm BackgroundTasks
    db: Session = Depends(deps.get_db)
):
    """
    Manually adjust stock quantity (e.g., after stock taking).
    """
    service = InventoryService(db)
    try:
        adjusted_stock = service.adjust_stock(adjustment)
        
        # [MỚI] Bắn tín hiệu làm mới giao diện tồn kho sau khi chỉnh sửa
        background_tasks.add_task(ws_manager.broadcast, "REFRESH_INVENTORY")
        
        return adjusted_stock
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))