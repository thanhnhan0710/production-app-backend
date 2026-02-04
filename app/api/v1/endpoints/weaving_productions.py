from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.api import deps
from app.schemas.weaving_production_schema import (
    WeavingProductionResponse,
    WeavingProductionCreate,
    WeavingProductionUpdate
)
from app.services.weaving_production_service import WeavingProductionService

router = APIRouter()

# =========================
# GET LIST (Đã cập nhật)
# =========================
@router.get("/", response_model=List[WeavingProductionResponse])
def read_weaving_productions(
    skip: int = 0,
    limit: int = 100,
    # [MỚI] Nhận tham số từ Frontend: ?weaving_ticket_id=123
    weaving_ticket_id: Optional[int] = Query(None, description="Lọc theo ID phiếu dệt"),
    db: Session = Depends(deps.get_db)
):
    """
    Lấy danh sách sản xuất dệt.
    Hỗ trợ lọc theo weaving_ticket_id để kiểm tra xem phiếu này đã cân hay chưa.
    """
    service = WeavingProductionService(db)
    # Truyền tham số vào service
    return service.get_multi(skip=skip, limit=limit, weaving_ticket_id=weaving_ticket_id)


# =========================
# CREATE
# =========================
@router.post("/", response_model=WeavingProductionResponse)
def create_weaving_production(
    production_in: WeavingProductionCreate,
    db: Session = Depends(deps.get_db)
):
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
    service = WeavingProductionService(db)
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
    service = WeavingProductionService(db)
    results = service.search(
        keyword=keyword, 
        machine_id=machine_id, 
        skip=skip, 
        limit=limit
    )
    return results