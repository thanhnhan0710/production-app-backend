from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from datetime import date

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
    db: Session = Depends(deps.get_db)
):
    service = PurchaseOrderService(db)
    return service.create(obj_in=po_in)

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
    db: Session = Depends(deps.get_db)
):
    service = PurchaseOrderService(db)
    po = service.get(po_id)
    if not po:
        raise HTTPException(status_code=404, detail="Purchase Order not found")
    
    return service.update(db_obj=po, obj_in=po_in)

@router.post("/{po_id}/items", response_model=POHeaderResponse)
def add_purchase_order_item(
    po_id: int, 
    item_in: PODetailCreate, 
    db: Session = Depends(deps.get_db)
):
    service = PurchaseOrderService(db)
    po = service.get(po_id)
    if not po:
        raise HTTPException(status_code=404, detail="Purchase Order not found")
        
    return service.add_item(po_id=po_id, item_in=item_in)

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
    db: Session = Depends(deps.get_db)
):
    """
    Xóa một Purchase Order (Chỉ áp dụng cho trạng thái Draft).
    """
    service = PurchaseOrderService(db)
    return service.delete(po_id)