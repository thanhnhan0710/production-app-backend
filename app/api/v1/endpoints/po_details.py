from fastapi import APIRouter, Depends, status, BackgroundTasks
from sqlalchemy.orm import Session

from app.api import deps
from app.core.websockets import ws_manager
from app.schemas.po_detail_schema import (
    PurchaseOrderDetailCreate,
    PurchaseOrderDetailUpdate, 
    PurchaseOrderDetailResponse
)
from app.services import po_detail_service

router = APIRouter()

@router.post("/po/{po_id}", response_model=PurchaseOrderDetailResponse, status_code=status.HTTP_201_CREATED)
def create_po_detail(
    po_id: int,
    detail_in: PurchaseOrderDetailCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db)
):
    """Thêm 1 dòng mặt hàng mới vào Đơn mua hàng (PO) đã có sẵn"""
    new_detail = po_detail_service.create_po_detail(db=db, po_id=po_id, detail_in=detail_in)
    
    # Broadcast REFRESH_PURCHASE_ORDERS để giao diện tự load lại tổng tiền
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_PURCHASE_ORDERS")
    return new_detail

@router.get("/{detail_id}", response_model=PurchaseOrderDetailResponse)
def read_po_detail_by_id(detail_id: int, db: Session = Depends(deps.get_db)):
    """Lấy thông tin của 1 dòng mặt hàng trong đơn"""
    return po_detail_service.get_po_detail_by_id(db=db, detail_id=detail_id)

@router.put("/{detail_id}", response_model=PurchaseOrderDetailResponse)
def update_po_detail(
    detail_id: int, 
    detail_in: PurchaseOrderDetailUpdate, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db)
):
    """Cập nhật thông tin (Số lượng, Đơn giá, Lịch trình giao hàng...) của 1 dòng mặt hàng"""
    updated_detail = po_detail_service.update_po_detail(db=db, detail_id=detail_id, detail_in=detail_in)
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_PURCHASE_ORDERS")
    return updated_detail

@router.delete("/{detail_id}")
def delete_po_detail(
    detail_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db)
):
    """Xóa 1 dòng chi tiết và tự động cập nhật lại tổng tiền cho Đơn hàng cha"""
    result = po_detail_service.delete_po_detail(db=db, detail_id=detail_id)
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_PURCHASE_ORDERS")
    return result