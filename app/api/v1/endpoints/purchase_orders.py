from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from app.api import deps
from app.models.purchase_order import POStatus
from app.schemas.purchase_order_schema import (
    POHeaderCreate, 
    POHeaderUpdate, 
    POHeaderResponse, # Giả định bạn đã tạo schema này để trả về dữ liệu (bao gồm cả list details)
    PODetailCreate
)
from app.services.purchase_order_service import PurchaseOrderService

router = APIRouter()

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
    """
    Lấy danh sách PO với các bộ lọc nâng cao (Tìm kiếm số PO, Vendor, Status, Ngày).
    """
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
    """
    Tạo mới một Purchase Order (kèm theo details nếu có).
    """
    service = PurchaseOrderService(db)
    return service.create(obj_in=po_in)

@router.get("/{po_id}", response_model=POHeaderResponse)
def read_purchase_order(
    po_id: int, 
    db: Session = Depends(deps.get_db)
):
    """
    Lấy chi tiết một PO theo ID.
    """
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
    """
    Cập nhật thông tin Header của PO (Trạng thái, Ghi chú, Ngày...).
    """
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
    """
    Thêm một dòng chi tiết (vật tư) vào PO đã tồn tại.
    """
    service = PurchaseOrderService(db)
    # Hàm add_item trong service đã xử lý check exists, nhưng ta có thể check trước để clear code
    po = service.get(po_id)
    if not po:
        raise HTTPException(status_code=404, detail="Purchase Order not found")
        
    return service.add_item(po_id=po_id, item_in=item_in)

@router.get("/by-number/{po_number}", response_model=POHeaderResponse)
def read_purchase_order_by_number(
    po_number: str, 
    db: Session = Depends(deps.get_db)
):
    """
    Tìm PO chính xác theo Số PO (PO Number).
    """
    service = PurchaseOrderService(db)
    po = service.get_by_number(po_number)
    if not po:
        raise HTTPException(status_code=404, detail="Purchase Order not found")
    return po