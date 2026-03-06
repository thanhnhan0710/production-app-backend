from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional

from app.api import deps
from app.core.websockets import ws_manager

from app.schemas.supplier_schema import SupplierCreate, SupplierUpdate, SupplierResponse
from app.services import supplier_service

router = APIRouter()

@router.get("/count", response_model=int)
def get_supplier_count(
    search: Optional[str] = None,
    category_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(deps.get_db)
):
    """Lấy tổng số lượng Nhà cung cấp"""
    return supplier_service.count_suppliers(
        db, search=search, category_id=category_id, is_active=is_active
    )

@router.get("/", response_model=List[SupplierResponse])
def read_suppliers(
    skip: int = 0, 
    limit: int = 100, 
    search: Optional[str] = None,
    category_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(deps.get_db)
):
    """Lấy danh sách Nhà cung cấp"""
    return supplier_service.get_suppliers(
        db, skip=skip, limit=limit, search=search, category_id=category_id, is_active=is_active
    )


@router.get("/{supplier_id}", response_model=SupplierResponse)
def read_supplier(supplier_id: int, db: Session = Depends(deps.get_db)):
    """Lấy chi tiết 1 Nhà cung cấp theo ID"""
    supplier = supplier_service.get_supplier_by_id(db, supplier_id)
    if not supplier:
        raise HTTPException(status_code=404, detail="Không tìm thấy Nhà cung cấp.")
    return supplier


@router.post("/", response_model=SupplierResponse)
def create_supplier(
    supplier_in: SupplierCreate, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db)
):
    """Thêm mới Nhà cung cấp"""
    new_supplier = supplier_service.create_supplier(db, supplier_in)
    
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_SUPPLIERS")
    
    return new_supplier


@router.put("/{supplier_id}", response_model=SupplierResponse)
def update_supplier(
    supplier_id: int, 
    supplier_in: SupplierUpdate, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db)
):
    """Cập nhật thông tin Nhà cung cấp"""
    updated_supplier = supplier_service.update_supplier(db, supplier_id, supplier_in)
    
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_SUPPLIERS")
    
    return updated_supplier


@router.delete("/{supplier_id}")
def delete_supplier(
    supplier_id: int, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db)
):
    """Xóa Nhà cung cấp"""
    result = supplier_service.delete_supplier(db, supplier_id)
    
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_SUPPLIERS")
    
    return result