from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.api import deps
from app.models.basket import BasketStatus
from app.schemas.basket_schema import (
    BasketResponse,
    BasketCreate,
    BasketUpdate
)
from app.services import basket_service

router = APIRouter()

# =========================
# GET LIST
# =========================
@router.get("/", response_model=List[BasketResponse])
def read_baskets(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db)
):
    """
    Lấy danh sách rổ (có phân trang)
    """
    return basket_service.get_baskets(db, skip, limit)

# =========================
# SEARCH
# =========================
@router.get("/search", response_model=List[BasketResponse])
def search_baskets(
    keyword: Optional[str] = None,
    status: Optional[BasketStatus] = None,
    min_weight: Optional[float] = None,
    max_weight: Optional[float] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db)
):
    """
    Tìm kiếm rổ theo Mã, NCC, Trạng thái hoặc Cân nặng
    """
    return basket_service.search_baskets(
        db=db,
        keyword=keyword,
        status=status,
        min_weight=min_weight,
        max_weight=max_weight,
        skip=skip,
        limit=limit
    )

# =========================
# GET DETAIL
# =========================
@router.get("/{basket_id}", response_model=BasketResponse)
def read_basket(
    basket_id: int,
    db: Session = Depends(deps.get_db)
):
    basket = basket_service.get_basket_by_id(db, basket_id)
    if not basket:
        raise HTTPException(status_code=404, detail="Basket not found")
    return basket

# =========================
# CREATE
# =========================
@router.post("/", response_model=BasketResponse)
def create_basket(
    basket_in: BasketCreate,
    db: Session = Depends(deps.get_db)
):
    """
    Tạo rổ mới. Mã rổ phải là duy nhất.
    """
    return basket_service.create_basket(db, basket_in)

# =========================
# UPDATE
# =========================
@router.put("/{basket_id}", response_model=BasketResponse)
def update_basket(
    basket_id: int,
    basket_in: BasketUpdate,
    db: Session = Depends(deps.get_db)
):
    """
    Cập nhật thông tin rổ. Nếu sửa mã rổ, sẽ check trùng.
    """
    # Service đã handle logic check trùng và throw HTTPException rồi
    # nên ở đây chỉ cần gọi hàm.
    return basket_service.update_basket(db, basket_id, basket_in)

# =========================
# DELETE
# =========================
@router.delete("/{basket_id}")
def delete_basket(
    basket_id: int,
    db: Session = Depends(deps.get_db)
):
    """
    Xóa rổ. Không thể xóa nếu rổ đang IN_USE.
    """
    return basket_service.delete_basket(db, basket_id)