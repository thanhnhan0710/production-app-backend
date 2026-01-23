from fastapi import APIRouter, Depends, HTTPException, Query
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
    db: Session = Depends(deps.get_db)
):
    service = MaterialReceiptService(db)
    return service.create(obj_in=receipt_in)

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
    db: Session = Depends(deps.get_db)
):
    service = MaterialReceiptService(db)
    return service.update(receipt_id, obj_in=receipt_in)

@router.delete("/{receipt_id}")
def delete_receipt(
    receipt_id: int, 
    db: Session = Depends(deps.get_db)
):
    service = MaterialReceiptService(db)
    return service.delete(receipt_id)

# --- DETAIL ENDPOINTS ---

@router.post("/{receipt_id}/details", response_model=MaterialReceiptDetailResponse)
def add_receipt_detail(
    receipt_id: int, 
    detail_in: MaterialReceiptDetailCreate, 
    db: Session = Depends(deps.get_db)
):
    service = MaterialReceiptService(db)
    return service.add_detail(receipt_id=receipt_id, detail_in=detail_in)

@router.put("/details/{detail_id}", response_model=MaterialReceiptDetailResponse)
def update_receipt_detail(
    detail_id: int, 
    detail_in: MaterialReceiptDetailUpdate, 
    db: Session = Depends(deps.get_db)
):
    service = MaterialReceiptService(db)
    return service.update_detail(detail_id=detail_id, obj_in=detail_in)

@router.delete("/details/{detail_id}")
def delete_receipt_detail(
    detail_id: int, 
    db: Session = Depends(deps.get_db)
):
    service = MaterialReceiptService(db)
    return service.delete_detail(detail_id=detail_id)