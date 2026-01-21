from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.api import deps
from app.schemas.bom_header_schema import (
    BOMHeaderResponse,
    BOMHeaderWithDetailsResponse, # Schema trả về kèm chi tiết
    BOMHeaderCreate,
    BOMHeaderUpdate
)
from app.services import bom_header_service

router = APIRouter()

# =========================
# GET LIST (ALL)
# =========================
@router.get("/", response_model=List[BOMHeaderResponse])
def read_bom_headers(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db)
):
    return bom_header_service.get_bom_headers(db, skip, limit)

# =========================
# SEARCH (ADVANCED)
# =========================
# Lưu ý: Đặt endpoint search TRƯỚC endpoint /{bom_id} để tránh nhầm lẫn đường dẫn
@router.get("/search", response_model=List[BOMHeaderResponse])
def search_bom_headers(
    keyword: Optional[str] = Query(None, description="Tìm theo Mã BOM hoặc Tên BOM"),
    product_id: Optional[int] = Query(None, description="Lọc BOM theo ID sản phẩm"),
    is_active: Optional[bool] = Query(None, description="Lọc theo trạng thái Active"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db)
):
    """
    Tìm kiếm nâng cao cho BOM Header.
    Ví dụ: /search?product_id=10&is_active=true
    """
    return bom_header_service.search_bom_headers(
        db, keyword, product_id, is_active, skip, limit
    )

# =========================
# GET ONE (WITH DETAILS)
# =========================
@router.get("/{bom_id}", response_model=BOMHeaderWithDetailsResponse)
def read_bom_header_by_id(
    bom_id: int,
    db: Session = Depends(deps.get_db)
):
    """
    Lấy chi tiết 1 BOM, bao gồm cả danh sách nguyên liệu (bom_details) bên trong.
    """
    bom = bom_header_service.get_bom_header_by_id(db, bom_id)
    if not bom:
        raise HTTPException(status_code=404, detail="BOM Header not found")
    return bom

# =========================
# CREATE
# =========================
@router.post("/", response_model=BOMHeaderResponse)
def create_bom_header(
    data: BOMHeaderCreate,
    db: Session = Depends(deps.get_db)
):
    # Logic: Nếu tạo BOM mới là Active, Service sẽ tự tắt các BOM cũ
    return bom_header_service.create_bom_header(db, data)

# =========================
# UPDATE
# =========================
@router.put("/{bom_id}", response_model=BOMHeaderResponse)
def update_bom_header(
    bom_id: int,
    data: BOMHeaderUpdate,
    db: Session = Depends(deps.get_db)
):
    updated_bom = bom_header_service.update_bom_header(db, bom_id, data)
    if not updated_bom:
        raise HTTPException(status_code=404, detail="BOM Header not found")
    return updated_bom

# =========================
# DELETE
# =========================
@router.delete("/{bom_id}")
def delete_bom_header(
    bom_id: int,
    db: Session = Depends(deps.get_db)
):
    success = bom_header_service.delete_bom_header(db, bom_id)
    if not success:
        raise HTTPException(status_code=404, detail="BOM Header not found")
    return {"message": "Deleted successfully"}