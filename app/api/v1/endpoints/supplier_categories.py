from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional

from app.api import deps
from app.core.websockets import ws_manager

from app.schemas.supplier_category_schema import SupplierCategoryCreate, SupplierCategoryUpdate, SupplierCategoryResponse
from app.services import supplier_category_service

router = APIRouter()

@router.get("/count", response_model=int)
def get_category_count(
    search: Optional[str] = None, 
    db: Session = Depends(deps.get_db)
):
    """Lấy tổng số lượng Loại nhà cung cấp"""
    return supplier_category_service.count_categories(db, search=search)

@router.get("/", response_model=List[SupplierCategoryResponse])
def read_categories(
    skip: int = 0, 
    limit: int = 100, 
    search: Optional[str] = None, 
    db: Session = Depends(deps.get_db)
):
    """Lấy danh sách Loại nhà cung cấp"""
    return supplier_category_service.get_categories(db, skip=skip, limit=limit, search=search)


@router.get("/{category_id}", response_model=SupplierCategoryResponse)
def read_category(category_id: int, db: Session = Depends(deps.get_db)):
    """Lấy thông tin Loại nhà cung cấp theo ID"""
    category = supplier_category_service.get_category_by_id(db, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Không tìm thấy Loại nhà cung cấp.")
    return category


@router.post("/", response_model=SupplierCategoryResponse)
def create_category(
    category_in: SupplierCategoryCreate, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db)
):
    """Tạo mới Loại nhà cung cấp"""
    new_category = supplier_category_service.create_category(db, category_in)
    
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_SUPPLIER_CATEGORIES")
    
    return new_category


@router.put("/{category_id}", response_model=SupplierCategoryResponse)
def update_category(
    category_id: int, 
    category_in: SupplierCategoryUpdate, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db)
):
    """Cập nhật Loại nhà cung cấp"""
    updated_category = supplier_category_service.update_category(db, category_id, category_in)
    
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_SUPPLIER_CATEGORIES")
    
    return updated_category


@router.delete("/{category_id}")
def delete_category(
    category_id: int, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db)
):
    """Xóa Loại nhà cung cấp"""
    result = supplier_category_service.delete_category(db, category_id)
    
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_SUPPLIER_CATEGORIES")
    
    return result