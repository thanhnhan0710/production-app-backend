from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session
from typing import Any, List, Optional, Dict
from datetime import date
from app.core.websockets import ws_manager

from app.api import deps
from app.models.purchase_order import POStatus
from app.schemas.purchase_order_schema import (
    POHeaderCreate, 
    POHeaderUpdate, 
    POHeaderResponse, 
    PODetailCreate
)
from app.services.purchase_order_service import PurchaseOrderService

router = APIRouter()

# [MỚI] Endpoint lấy số PO tự động
@router.get("/next-number", response_model=Dict[str, str])
def get_next_po_number(db: Session = Depends(deps.get_db)):
    """
    Sinh số PO tiếp theo: V[YY]xxxx (VD: V260001).
    """
    service = PurchaseOrderService(db)
    new_number = service.generate_next_po_number()
    return {"po_number": new_number}

@router.get("/", response_model=List[POHeaderResponse])
def read_purchase_orders(
    skip: int = 0, 
    limit: int = 100, 
    search: Optional[str] = None,
    vendor_id: Optional[int] = None,
    status: Optional[POStatus] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    db: Session = Depends(deps.get_db)
):
    service = PurchaseOrderService(db)
    return service.get_multi(
        skip=skip, 
        limit=limit, 
        search=search, 
        vendor_id=vendor_id, 
        status=status,
        from_date=from_date,
        to_date=to_date
    )

@router.post("/", response_model=POHeaderResponse)
def create_purchase_order(
    po_in: POHeaderCreate,
    background_tasks: BackgroundTasks, # [CẬP NHẬT] Thêm BackgroundTasks
    db: Session = Depends(deps.get_db)
):
    service = PurchaseOrderService(db)
    new_po = service.create(obj_in=po_in)
    
    # [CẬP NHẬT] Bắn tín hiệu WebSocket
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_PURCHASE_ORDERS")
    return new_po

@router.get("/{po_id}", response_model=POHeaderResponse)
def read_purchase_order(
    po_id: int, 
    db: Session = Depends(deps.get_db)
):
    service = PurchaseOrderService(db)
    po = service.get(po_id)
    if not po:
        raise HTTPException(status_code=404, detail="Purchase Order not found")
    return po

@router.put("/{po_id}", response_model=POHeaderResponse)
def update_purchase_order(
    po_id: int, 
    po_in: POHeaderUpdate,
    background_tasks: BackgroundTasks, # [CẬP NHẬT] Thêm BackgroundTasks
    db: Session = Depends(deps.get_db)
):
    service = PurchaseOrderService(db)
    po = service.get(po_id)
    if not po:
        raise HTTPException(status_code=404, detail="Purchase Order not found")
    
    updated_po = service.update(db_obj=po, obj_in=po_in)
    
    # [CẬP NHẬT] Bắn tín hiệu WebSocket
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_PURCHASE_ORDERS")
    return updated_po

@router.post("/{po_id}/items", response_model=POHeaderResponse)
def add_purchase_order_item(
    po_id: int, 
    item_in: PODetailCreate,
    background_tasks: BackgroundTasks, # [CẬP NHẬT] Thêm BackgroundTasks
    db: Session = Depends(deps.get_db)
):
    service = PurchaseOrderService(db)
    po = service.get(po_id)
    if not po:
        raise HTTPException(status_code=404, detail="Purchase Order not found")
        
    po_with_item = service.add_item(po_id=po_id, item_in=item_in)
    
    # [CẬP NHẬT] Bắn tín hiệu WebSocket
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_PURCHASE_ORDERS")
    return po_with_item

@router.get("/by-number/{po_number}", response_model=POHeaderResponse)
def read_purchase_order_by_number(
    po_number: str, 
    db: Session = Depends(deps.get_db)
):
    service = PurchaseOrderService(db)
    po = service.get_by_number(po_number)
    if not po:
        raise HTTPException(status_code=404, detail="Purchase Order not found")
    return po

@router.delete("/{po_id}")
def delete_purchase_order(
    po_id: int,
    background_tasks: BackgroundTasks, # [CẬP NHẬT] Thêm BackgroundTasks
    db: Session = Depends(deps.get_db)
):
    """
    Xóa một Purchase Order (Chỉ áp dụng cho trạng thái Draft).
    """
    service = PurchaseOrderService(db)
    result = service.delete(po_id)
    
    # [CẬP NHẬT] Bắn tín hiệu WebSocket
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_PURCHASE_ORDERS")
    return result

# -------------------------------------------------------------------
# IMPORT EXCEL
# -------------------------------------------------------------------
@router.post("/import", status_code=200)
def import_po_excel(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(deps.get_db)
) -> Dict[str, Any]:
    """
    Import Đơn hàng (PO) và Tờ khai hải quan từ file Excel.
    """
    if not file.filename.endswith(('.xls', '.xlsx')):
        raise HTTPException(status_code=400, detail="Chỉ chấp nhận file .xls hoặc .xlsx")
        
    service = PurchaseOrderService(db)
    result = service.import_po_and_declaration_from_excel(file)
    
    if result.get("status"):
        # Cập nhật thành công -> Báo Frontend làm mới danh sách PO và Tờ khai
        background_tasks.add_task(ws_manager.broadcast, "REFRESH_PURCHASE_ORDERS")
        background_tasks.add_task(ws_manager.broadcast, "REFRESH_DECLARATIONS")
        return result
    else:
        raise HTTPException(status_code=400, detail=result.get("message"))