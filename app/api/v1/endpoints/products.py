from fastapi import APIRouter, Depends, File, HTTPException, BackgroundTasks, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional

from app.api import deps
from app.schemas.product_schema import ProductResponse, ProductCreate, ProductUpdate
from app.services import product_service
from app.core.websockets import ws_manager

router = APIRouter()

@router.get("/", response_model=List[ProductResponse])
def read_products(
    skip: int = 0,
    limit: int = 100,
    product_type_id: Optional[int] = None, # Cho phép lọc danh sách theo Loại (ID)
    db: Session = Depends(deps.get_db)
):
    return product_service.get_products(db, skip, limit, product_type_id)

@router.post("/", response_model=ProductResponse)
def create_product(
    product: ProductCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db)
):
    new_product = product_service.create_product(db, product)
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_PRODUCTS")
    return new_product

@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    product: ProductUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db)
):
    updated_product = product_service.update_product(db, product_id, product)
    if not updated_product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_PRODUCTS")
    return updated_product

@router.delete("/{product_id}")
def delete_product(
    product_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db)
):
    success = product_service.delete_product(db, product_id)
    if not success:
        raise HTTPException(status_code=404, detail="Product not found")
    
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_PRODUCTS")
    return {"message": "Deleted successfully"}

@router.get("/search", response_model=List[ProductResponse])
def search_products(
    keyword: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db)
):
    return product_service.search_products(db, keyword, skip, limit)

@router.post("/import", status_code=200)
def import_excel(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(deps.get_db)
):
    """
    Import danh sách sản phẩm. Cột 'Loại sản phẩm' sẽ tự động dò tìm hoặc tạo mới ProductType.
    """
    if not file.filename.endswith(('.xls', '.xlsx')):
        raise HTTPException(status_code=400, detail="Chỉ chấp nhận định dạng .xls hoặc .xlsx")
        
    result = product_service.import_products_from_excel(db, file)
    
    if result.get("status"):
        if result.get("success_count", 0) > 0:
            # Phát tín hiệu tải lại Danh sách sản phẩm
            background_tasks.add_task(ws_manager.broadcast, "REFRESH_PRODUCTS")
            # Phát tín hiệu tải lại Danh sách loại sản phẩm (nếu file Excel có loại mới)
            background_tasks.add_task(ws_manager.broadcast, "REFRESH_PRODUCT_TYPES")
        return result
    else:
        raise HTTPException(status_code=400, detail=result.get("message"))

@router.get("/export", status_code=200)
def export_excel(db: Session = Depends(deps.get_db)):
    output = product_service.export_products_to_excel(db)
    
    headers = {
        'Content-Disposition': 'attachment; filename="ITemCode.xlsx"'
    }
    
    return StreamingResponse(
        output, 
        headers=headers, 
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )