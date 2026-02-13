from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks # [THÊM] BackgroundTasks
from sqlalchemy.orm import Session
from typing import List

from app.api import deps
from app.schemas.supplier_schema import SupplierResponse, SupplierCreate, SupplierUpdate
from app.services import supplier_service

# --- [THÊM] Import ws_manager để gọi WebSocket ---
from app.core.websockets import ws_manager

router = APIRouter()

# =========================
# GET LIST
# =========================
@router.get("/", response_model=List[SupplierResponse])
def read_suppliers(skip: int = 0, limit: int = 100, db: Session = Depends(deps.get_db)):
    return supplier_service.get_suppliers(db, skip=skip, limit=limit)

# =========================
# CREATE
# =========================
@router.post("/", response_model=SupplierResponse)
def create_supplier(
    sup: SupplierCreate, 
    background_tasks: BackgroundTasks, # [THÊM] BackgroundTasks
    db: Session = Depends(deps.get_db)
):
    new_supplier = supplier_service.create_supplier(db, sup)
    
    # [THÊM] Bắn tín hiệu WebSocket để các máy khác cập nhật danh sách Nhà cung cấp
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_SUPPLIERS")
    
    return new_supplier

# =========================
# UPDATE
# =========================
@router.put("/{sup_id}", response_model=SupplierResponse)
def update_supplier(
    sup_id: int, 
    sup: SupplierUpdate, 
    background_tasks: BackgroundTasks, # [THÊM] BackgroundTasks
    db: Session = Depends(deps.get_db)
):
    updated_sup = supplier_service.update_supplier(db, sup_id, sup)
    if not updated_sup:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    # [THÊM] Bắn tín hiệu WebSocket
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_SUPPLIERS")
    
    return updated_sup

# =========================
# DELETE
# =========================
@router.delete("/{sup_id}")
def delete_supplier(
    sup_id: int, 
    background_tasks: BackgroundTasks, # [THÊM] BackgroundTasks
    db: Session = Depends(deps.get_db)
):
    success = supplier_service.delete_supplier(db, sup_id)
    if not success:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    # [THÊM] Bắn tín hiệu WebSocket
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_SUPPLIERS")
    
    return {"message": "Deleted successfully"}

# =========================
# SEARCH
# =========================
@router.get("/search", response_model=List[SupplierResponse])
def search_suppliers(
    keyword: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db)
):
    return supplier_service.search_suppliers(db, keyword, skip, limit)