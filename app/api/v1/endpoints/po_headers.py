from fastapi import APIRouter, Depends, Query, status, BackgroundTasks
from fastapi.responses import StreamingResponse # [MỚI]
from sqlalchemy.orm import Session
from typing import List, Optional
import datetime

from app.api import deps
from app.core.websockets import ws_manager
from app.schemas.po_header_schema import (
    PurchaseOrderHeaderCreate, 
    PurchaseOrderHeaderUpdate, 
    PurchaseOrderHeaderResponse
)
from app.services import po_header_service

router = APIRouter()

@router.get("/next-number", response_model=str)
def get_next_po_number(db: Session = Depends(deps.get_db)):
    return po_header_service.get_next_po_number(db)

# --- [MỚI]: API TẢI FILE EXCEL THEO DÕI ---
@router.get("/export", response_class=StreamingResponse)
def export_purchase_orders(
    vendor_id: Optional[int] = Query(None, description="Lọc theo ID nhà cung cấp"),
    status_id: Optional[int] = Query(None, description="Lọc theo Trạng thái"),
    search: Optional[str] = Query(None, description="Tìm theo số PO"),
    db: Session = Depends(deps.get_db)
):
    """Xuất file Excel chứa chi tiết lịch trình giao hàng"""
    excel_stream = po_header_service.export_excel_purchase_orders(db=db, vendor_id=vendor_id, status_id=status_id, search=search)
    
    filename = f"TheoDoiPO_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    return StreamingResponse(
        excel_stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get("/count", response_model=int)
def get_purchase_orders_count(
    vendor_id: Optional[int] = Query(None, description="Lọc theo ID nhà cung cấp"),
    status_id: Optional[int] = Query(None, description="Lọc theo Trạng thái"), # [MỚI]
    search: Optional[str] = Query(None, description="Tìm theo số PO"),
    db: Session = Depends(deps.get_db)
):
    return po_header_service.count_purchase_orders(db=db, vendor_id=vendor_id, status_id=status_id, search=search)

@router.get("/", response_model=List[PurchaseOrderHeaderResponse])
def read_purchase_orders(
    skip: int = 0,
    limit: int = 100,
    vendor_id: Optional[int] = Query(None, description="Lọc theo ID nhà cung cấp"),
    status_id: Optional[int] = Query(None, description="Lọc theo Trạng thái"), # [MỚI]
    search: Optional[str] = Query(None, description="Tìm theo số PO"),
    db: Session = Depends(deps.get_db)
):
    return po_header_service.get_purchase_orders(
        db=db, skip=skip, limit=limit, vendor_id=vendor_id, status_id=status_id, search=search
    )

@router.get("/{po_id}", response_model=PurchaseOrderHeaderResponse)
def read_purchase_order_by_id(po_id: int, db: Session = Depends(deps.get_db)):
    return po_header_service.get_po_by_id(db=db, po_id=po_id)

@router.post("/", response_model=PurchaseOrderHeaderResponse, status_code=status.HTTP_201_CREATED)
def create_purchase_order(
    po_in: PurchaseOrderHeaderCreate, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db)
):
    new_po = po_header_service.create_purchase_order(db=db, po_in=po_in)
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_PURCHASE_ORDERS")
    return new_po

@router.put("/{po_id}", response_model=PurchaseOrderHeaderResponse)
def update_purchase_order(
    po_id: int, 
    po_update: PurchaseOrderHeaderUpdate, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db)
):
    updated_po = po_header_service.update_po_header(db=db, po_id=po_id, po_update=po_update)
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_PURCHASE_ORDERS")
    return updated_po

@router.delete("/{po_id}")
def delete_purchase_order(
    po_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db)
):
    result = po_header_service.delete_po_header(db=db, po_id=po_id)
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_PURCHASE_ORDERS")
    return result