from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.api import deps
from app.schemas.weaving_production_schema import (
    WeavingProductionResponse,
    WeavingProductionCreate,
    WeavingProductionUpdate
)
# Import class Service đã viết ở bước trước
from app.services.weaving_production_service import WeavingProductionService

router = APIRouter()

# =========================
# GET LIST
# =========================
@router.get("/", response_model=List[WeavingProductionResponse])
def read_weaving_productions(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db)
):
    """
    Lấy danh sách sản xuất dệt.
    Kết quả bao gồm thông tin chi tiết: Tên máy, Line, Rổ, Ca, Người cập nhật.
    """
    service = WeavingProductionService(db)
    return service.get_multi(skip=skip, limit=limit)


# =========================
# CREATE
# =========================
@router.post("/", response_model=WeavingProductionResponse)
def create_weaving_production(
    production_in: WeavingProductionCreate,
    db: Session = Depends(deps.get_db)
):
    """
    Tạo mới một bản ghi sản xuất.
    """
    service = WeavingProductionService(db)
    return service.create(obj_in=production_in)


# =========================
# UPDATE
# =========================
@router.put("/{production_id}", response_model=WeavingProductionResponse)
def update_weaving_production(
    production_id: int,
    production_in: WeavingProductionUpdate,
    db: Session = Depends(deps.get_db)
):
    """
    Cập nhật thông tin sản xuất (khối lượng, phế, máy, rổ...).
    """
    service = WeavingProductionService(db)
    updated_production = service.update(production_id=production_id, obj_in=production_in)
    
    if not updated_production:
        raise HTTPException(status_code=404, detail="Weaving Production record not found")
    
    return updated_production


# =========================
# DELETE
# =========================
@router.delete("/{production_id}")
def delete_weaving_production(
    production_id: int,
    db: Session = Depends(deps.get_db)
):
    """
    Xóa bản ghi sản xuất.
    """
    service = WeavingProductionService(db)
    # Lưu ý: Cần bổ sung hàm delete vào Service nếu chưa có
    # Giả định hàm service.delete(id) trả về True nếu xóa thành công, False nếu không tìm thấy
    success = service.delete(production_id) 
    
    if not success:
        raise HTTPException(status_code=404, detail="Weaving Production record not found")
    
    return {"message": "Deleted successfully"}


# =========================
# SEARCH
# =========================
@router.get("/search", response_model=List[WeavingProductionResponse])
def search_weaving_productions(
    keyword: Optional[str] = None,
    machine_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db)
):
    """
    Tìm kiếm bản ghi sản xuất.
    - Có thể tìm theo keyword (nếu logic service hỗ trợ tìm theo tên máy/tên rổ)
    - Hoặc tìm chính xác theo machine_id
    """
    service = WeavingProductionService(db)
    
    # Lưu ý: Cần bổ sung hàm search vào Service
    # Hàm này sẽ join với bảng Machine/Basket để tìm theo tên
    results = service.search(
        keyword=keyword, 
        machine_id=machine_id, 
        skip=skip, 
        limit=limit
    )
    
    return results