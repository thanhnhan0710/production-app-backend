from fastapi import APIRouter, Depends, File, HTTPException, BackgroundTasks, UploadFile # [THÊM] BackgroundTasks
from fastapi.responses import StreamingResponse
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

# =========================
# IMPORT EXCEL
# =========================
@router.post("/import", status_code=200)
def import_excel(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(deps.get_db)
):
    """
    Upload file Excel để import danh sách Sản phẩm.
    """
    if not file.filename.endswith(('.xls', '.xlsx')):
        raise HTTPException(status_code=400, detail="Chỉ chấp nhận định dạng .xls hoặc .xlsx")
        
    result = product_service.import_products_from_excel(db, file)
    
    if result.get("status"):
        if result.get("success_count", 0) > 0:
            # Bắn tín hiệu WebSocket để giao diện tự làm mới
            background_tasks.add_task(ws_manager.broadcast, "REFRESH_PRODUCTS")
        return result
    else:
        raise HTTPException(status_code=400, detail=result.get("message"))

# =========================
# EXPORT EXCEL
# =========================
@router.get("/export", status_code=200)
def export_excel(db: Session = Depends(deps.get_db)):
    """
    Tải xuống file Excel danh sách sản phẩm.
    """
    output = product_service.export_products_to_excel(db)
    
    headers = {
        'Content-Disposition': 'attachment; filename="Danh_Muc_San_Pham.xlsx"'
    }
    
    return StreamingResponse(
        output, 
        headers=headers, 
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )