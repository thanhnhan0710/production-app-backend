from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.api import deps
from app.schemas.inventory_schema import (
    InventoryStockResponse, 
    InventoryAdjustment
)
from app.services.inventory_service import InventoryService

router = APIRouter()

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
    db: Session = Depends(deps.get_db)
):
    """
    Manually adjust stock quantity (e.g., after stock taking).
    """
    service = InventoryService(db)
    try:
        return service.adjust_stock(adjustment)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))