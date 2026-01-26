from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from app.db.session import get_db
from app.models.bom_header import BOMHeader

from app.schemas.bom_schema import (
    BOMHeaderCreate,
    BOMHeaderUpdate,
    BOMHeaderResponse
)
from app.services.bom_service import BOMService

router = APIRouter()

# -------------------------------------------------------------------
# 1. TÌM KIẾM & DANH SÁCH BOM
# -------------------------------------------------------------------
@router.get("/", response_model=List[BOMHeaderResponse])
def read_boms(
    db: Session = Depends(get_db),
    product_code: Optional[str] = Query(None, description="Tìm theo mã sản phẩm (Item Code)"),
    year: Optional[int] = Query(None, description="Tìm theo năm áp dụng (VD: 2026)"), # [THAY ĐỔI] Thay bom_code bằng year
    is_active: Optional[bool] = Query(None, description="Lọc theo trạng thái kích hoạt"),
) -> Any:
    """
    Lấy danh sách BOM Yarn.
    Hỗ trợ tìm kiếm theo Mã sản phẩm (product_code) và Năm (year).
    """
    boms = BOMService.search_boms(
        db=db, 
        product_code=product_code, 
        year=year, 
        is_active=is_active
    )
    return boms

# -------------------------------------------------------------------
# 2. TẠO MỚI BOM (Tự động tính toán định mức)
# -------------------------------------------------------------------
@router.post("/", response_model=BOMHeaderResponse)
def create_bom(
    bom_in: BOMHeaderCreate,
    db: Session = Depends(get_db)
) -> Any:
    """
    Tạo mới một BOM Yarn cho một Năm cụ thể.
    
    - Hệ thống sẽ kiểm tra xem Product + Year đã tồn tại chưa.
    - Hệ thống tự động tính toán trọng lượng sợi và định mức (g/m).
    """
    try:
        new_bom = BOMService.create_bom(db=db, bom_in=bom_in)
        return new_bom
    except HTTPException as e:
        raise e
    except Exception as e:
        # Bắt các lỗi không mong muốn khác
        raise HTTPException(status_code=400, detail=str(e))

# -------------------------------------------------------------------
# 3. LẤY CHI TIẾT 1 BOM (Theo ID)
# -------------------------------------------------------------------
@router.get("/{bom_id}", response_model=BOMHeaderResponse)
def read_bom_by_id(
    bom_id: int,
    db: Session = Depends(get_db)
) -> Any:
    """
    Xem chi tiết cấu trúc của một BOM cụ thể.
    """
    # [QUAN TRỌNG] Thêm joinedload để lấy luôn danh sách bom_details
    bom = db.query(BOMHeader)\
        .options(joinedload(BOMHeader.bom_details))\
        .filter(BOMHeader.bom_id == bom_id)\
        .first()
        
    if not bom:
        raise HTTPException(status_code=404, detail="BOM not found")
    return bom

# -------------------------------------------------------------------
# 4. CẬP NHẬT BOM (Tính toán lại toàn bộ)
# -------------------------------------------------------------------
@router.put("/{bom_id}", response_model=BOMHeaderResponse)
def update_bom(
    bom_id: int,
    bom_in: BOMHeaderUpdate,
    db: Session = Depends(get_db)
) -> Any:
    """
    Cập nhật thông tin BOM.
    
    - Nếu thay đổi `applicable_year`, hệ thống sẽ check trùng lặp.
    - Nếu gửi kèm `details`, hệ thống sẽ tính toán lại toàn bộ định mức.
    """
    try:
        updated_bom = BOMService.update_bom(db=db, bom_id=bom_id, bom_update=bom_in)
        return updated_bom
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# -------------------------------------------------------------------
# 5. XÓA BOM
# -------------------------------------------------------------------
@router.delete("/{bom_id}", response_model=dict)
def delete_bom(
    bom_id: int,
    db: Session = Depends(get_db)
) -> Any:
    """
    Xóa cứng một BOM khỏi hệ thống.
    """
    success = BOMService.delete_bom(db=db, bom_id=bom_id)
    if not success:
        raise HTTPException(status_code=404, detail="BOM not found")
    
    return {"message": "BOM deleted successfully", "bom_id": bom_id}