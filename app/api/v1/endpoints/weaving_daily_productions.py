from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from app.api import deps
from app.schemas.weaving_daily_production_schema import (
    WeavingProductionResponse,
    WeavingProductionCreate,
    WeavingProductionUpdate
)
from app.services import weaving_daily_production_service

router = APIRouter()


# =========================
# GET LIST (ALL)
# =========================
@router.get("/", response_model=List[WeavingProductionResponse])
def read_productions(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db)
):
    """
    Lấy danh sách sản lượng dệt (Mặc định sắp xếp ngày mới nhất).
    """
    return weaving_daily_production_service.get_productions(
        db, skip=skip, limit=limit
    )


# =========================
# SEARCH (ADVANCED)
# =========================
@router.get("/search", response_model=List[WeavingProductionResponse])
def search_productions(
    keyword: Optional[str] = None,      # Tìm theo mã/tên sản phẩm
    product_id: Optional[int] = None,   # Lọc theo ID sản phẩm
    from_date: Optional[date] = None,   # Lọc từ ngày
    to_date: Optional[date] = None,     # Lọc đến ngày
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db)
):
    """
    Tìm kiếm nâng cao: Theo từ khóa sản phẩm, ID sản phẩm, hoặc khoảng thời gian.
    """
    return weaving_daily_production_service.search_productions(
        db=db,
        keyword=keyword,
        product_id=product_id,
        from_date=from_date,
        to_date=to_date,
        skip=skip,
        limit=limit
    )


# =========================
# CREATE
# =========================
@router.post("/", response_model=WeavingProductionResponse)
def create_production(
    production: WeavingProductionCreate,
    db: Session = Depends(deps.get_db)
):
    """
    Tạo mới một bản ghi sản lượng (Thường dùng nếu nhập tay hoặc test).
    Lưu ý: Nếu trùng (date + product_id) sẽ báo lỗi IntegrityError.
    """
    # Bạn có thể thêm try/catch ở đây để bắt lỗi trùng lặp nếu muốn trả về 400 đẹp hơn
    return weaving_daily_production_service.create_production(db, production)


# =========================
# GET ONE (BY ID)
# =========================
@router.get("/{production_id}", response_model=WeavingProductionResponse)
def read_production(
    production_id: int,
    db: Session = Depends(deps.get_db)
):
    """
    Lấy chi tiết một bản ghi theo ID.
    """
    db_production = weaving_daily_production_service.get_production(db, production_id)
    if not db_production:
        raise HTTPException(status_code=404, detail="Production record not found")
    return db_production


# =========================
# UPDATE
# =========================
@router.put("/{production_id}", response_model=WeavingProductionResponse)
def update_production(
    production_id: int,
    production_in: WeavingProductionUpdate,
    db: Session = Depends(deps.get_db)
):
    """
    Cập nhật thông tin sản lượng (Ví dụ: điều chỉnh số liệu sai lệch).
    """
    updated_production = weaving_daily_production_service.update_production(
        db, production_id, production_in
    )
    if not updated_production:
        raise HTTPException(status_code=404, detail="Production record not found")
    return updated_production


# =========================
# DELETE
# =========================
@router.delete("/{production_id}")
def delete_production(
    production_id: int,
    db: Session = Depends(deps.get_db)
):
    """
    Xóa một bản ghi sản lượng.
    """
    success = weaving_daily_production_service.delete_production(db, production_id)
    if not success:
        raise HTTPException(status_code=404, detail="Production record not found")
    return {"message": "Deleted successfully"}

# =========================
# CALCULATE MANUAL (TÍNH TOÁN LẠI)
# =========================
@router.post("/calculate-manual")
def manual_calculation(
    target_date: date,
    db: Session = Depends(deps.get_db)
):
    """API này để chạy thủ công, cập nhật dữ liệu cho những ngày cũ"""
    return weaving_daily_production_service.calculate_daily_production(db, target_date)