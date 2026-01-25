from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

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
    bom_code: Optional[str] = Query(None, description="Tìm theo mã BOM"),
    is_active: Optional[bool] = Query(None, description="Lọc theo trạng thái kích hoạt"),
) -> Any:
    """
    Lấy danh sách BOM Yarn.
    Hỗ trợ tìm kiếm theo Mã sản phẩm (product_code) hoặc Mã BOM.
    """
    boms = BOMService.search_boms(
        db=db, 
        product_code=product_code, 
        bom_code=bom_code, 
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
    Tạo mới một BOM Yarn.
    
    - Hệ thống sẽ **tự động tính toán** trọng lượng sợi, định mức (g/m) 
      dựa trên số lượng sợi (threads) và loại sợi (yarn_type_name) được gửi lên.
    - Input: Danh sách chi tiết sợi.
    - Output: BOM hoàn chỉnh với các con số đã được tính toán.
    """
    try:
        new_bom = BOMService.create_bom(db=db, bom_in=bom_in)
        return new_bom
    except Exception as e:
        # Bắt các lỗi logic từ Service (ví dụ: Không tìm thấy sản phẩm)
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
    bom = db.query(BOMHeader).filter(BOMHeader.bom_id == bom_id).first()
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
    
    LƯU Ý: Nếu gửi kèm danh sách `details` mới, hệ thống sẽ:
    1. Xóa toàn bộ chi tiết cũ của BOM này.
    2. Tính toán lại định mức cho danh sách chi tiết mới.
    3. Lưu lại vào DB.
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