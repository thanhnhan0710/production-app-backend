from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks # [THÊM] BackgroundTasks
from sqlalchemy.orm import Session
from typing import List

from app.api import deps
from app.schemas.product_schema import (
    ProductResponse,
    ProductCreate,
    ProductUpdate
)
from app.services import product_service

# --- [THÊM] Import ws_manager để gọi WebSocket ---
from app.core.websockets import ws_manager

router = APIRouter()


# =========================
# GET LIST
# =========================
@router.get("/", response_model=List[ProductResponse])
def read_products(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db)
):
    return product_service.get_products(db, skip, limit)


# =========================
# CREATE (Thêm mới)
# =========================
@router.post("/", response_model=ProductResponse)
def create_product(
    product: ProductCreate,
    background_tasks: BackgroundTasks, # [THÊM] BackgroundTasks
    db: Session = Depends(deps.get_db)
):
    new_product = product_service.create_product(db, product)
    
    # [THÊM] Bắn tín hiệu WebSocket để các màn hình Danh mục sản phẩm tải lại dữ liệu
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_PRODUCTS")
    
    return new_product


# =========================
# UPDATE (Cập nhật)
# =========================
@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    product: ProductUpdate,
    background_tasks: BackgroundTasks, # [THÊM] BackgroundTasks
    db: Session = Depends(deps.get_db)
):
    updated_product = product_service.update_product(
        db, product_id, product
    )
    if not updated_product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # [THÊM] Bắn tín hiệu WebSocket
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_PRODUCTS")
    
    return updated_product


# =========================
# DELETE (Xóa)
# =========================
@router.delete("/{product_id}")
def delete_product(
    product_id: int,
    background_tasks: BackgroundTasks, # [THÊM] BackgroundTasks
    db: Session = Depends(deps.get_db)
):
    success = product_service.delete_product(db, product_id)
    if not success:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # [THÊM] Bắn tín hiệu WebSocket
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_PRODUCTS")
    
    return {"message": "Deleted successfully"}


# =========================
# SEARCH
# =========================
@router.get("/search", response_model=List[ProductResponse])
def search_products(
    keyword: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db)
):
    return product_service.search_products(
        db, keyword, skip, limit
    )