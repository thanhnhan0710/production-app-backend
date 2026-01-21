from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.api import deps
from app.models.bom_detail import BOMComponentType
from app.schemas.bom_detail_schema import (
    BOMDetailResponse,
    BOMDetailCreate,
    BOMDetailUpdate
)
from app.services import bom_detail_service

router = APIRouter()

# =========================
# SEARCH / FILTER (TRACEABILITY)
# =========================
@router.get("/search", response_model=List[BOMDetailResponse])
def search_bom_details(
    bom_id: Optional[int] = Query(None, description="Lọc theo BOM ID"),
    material_id: Optional[int] = Query(None, description="Lọc theo Nguyên liệu (Traceability)"),
    component_type: Optional[BOMComponentType] = Query(None, description="Lọc theo loại sợi (Warp/Weft...)"),
    keyword: Optional[str] = Query(None, description="Tìm trong ghi chú"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db)
):
    """
    Tìm kiếm chi tiết BOM. 
    Hữu ích khi muốn tìm: "Nguyên liệu A này đang được dùng trong những BOM nào?"
    """
    return bom_detail_service.search_bom_details(
        db, bom_id, material_id, component_type, keyword, skip, limit
    )

# =========================
# GET BY BOM ID (Shortcut)
# =========================
@router.get("/by-bom/{bom_id}", response_model=List[BOMDetailResponse])
def read_details_by_bom(
    bom_id: int,
    db: Session = Depends(deps.get_db)
):
    """Lấy nhanh toàn bộ chi tiết của 1 BOM cụ thể"""
    return bom_detail_service.get_details_by_bom_id(db, bom_id)

# =========================
# CREATE
# =========================
@router.post("/", response_model=BOMDetailResponse)
def create_bom_detail(
    data: BOMDetailCreate,
    db: Session = Depends(deps.get_db)
):
    return bom_detail_service.create_bom_detail(db, data)

# =========================
# UPDATE
# =========================
@router.put("/{detail_id}", response_model=BOMDetailResponse)
def update_bom_detail(
    detail_id: int,
    data: BOMDetailUpdate,
    db: Session = Depends(deps.get_db)
):
    updated_detail = bom_detail_service.update_bom_detail(db, detail_id, data)
    if not updated_detail:
        raise HTTPException(status_code=404, detail="BOM Detail not found")
    return updated_detail

# =========================
# DELETE ONE
# =========================
@router.delete("/{detail_id}")
def delete_bom_detail(
    detail_id: int,
    db: Session = Depends(deps.get_db)
):
    success = bom_detail_service.delete_bom_detail(db, detail_id)
    if not success:
        raise HTTPException(status_code=404, detail="BOM Detail not found")
    return {"message": "Deleted successfully"}

# =========================
# DELETE ALL IN BOM
# =========================
@router.delete("/delete-all/{bom_id}")
def delete_all_details_in_bom(
    bom_id: int,
    db: Session = Depends(deps.get_db)
):
    """Xóa sạch chi tiết của 1 BOM (Dùng khi muốn reset nhập lại)"""
    bom_detail_service.delete_all_details_in_bom(db, bom_id)
    return {"message": f"All details in BOM {bom_id} deleted successfully"}