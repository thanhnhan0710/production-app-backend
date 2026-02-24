from typing import Any, List, Optional, Dict
from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload
from app.core.websockets import ws_manager # Import ws_manager

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
    year: Optional[int] = Query(None, description="Tìm theo năm áp dụng (VD: 2026)"), 
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
    background_tasks: BackgroundTasks, # [THÊM]
    db: Session = Depends(get_db)
) -> Any:
    """
    Tạo mới một BOM Yarn cho một Năm cụ thể.
    
    - Hệ thống sẽ kiểm tra xem Product + Year đã tồn tại chưa.
    - Hệ thống tự động tính toán trọng lượng sợi và định mức (g/m).
    """
    try:
        new_bom = BOMService.create_bom(db=db, bom_in=bom_in)
        # [THÊM] Phát tín hiệu làm mới danh sách BOM
        background_tasks.add_task(ws_manager.broadcast, "REFRESH_BOMS")
        return new_bom
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ===================================================================
# 8. XUẤT FILE EXCEL
# ===================================================================
@router.get("/export", status_code=200)
def export_excel(db: Session = Depends(get_db)):
    """
    Tải xuống file Excel chứa toàn bộ dữ liệu BOM.
    """
    output = BOMService.export_boms_to_excel(db)
    
    headers = {
        'Content-Disposition': 'attachment; filename="BOM YARN.xlsx"'
    }
    
    return StreamingResponse(
        output, 
        headers=headers, 
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

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
    bom = db.query(BOMHeader)\
        .options(joinedload(BOMHeader.bom_details))\
        .filter(BOMHeader.bom_id == bom_id)\
        .first()
        
    if not bom:
        raise HTTPException(status_code=404, detail="BOM not found")
    return bom

# -------------------------------------------------------------------
# 4. [MỚI] LẤY BẢNG TỔNG HỢP SỐ CUỘN (SUMMARY)
# -------------------------------------------------------------------
@router.get("/{bom_id}/summary", response_model=List[Dict[str, Any]])
def get_bom_summary(
    bom_id: int,
    db: Session = Depends(get_db)
) -> Any:
    """
    API trả về bảng tổng hợp 'Số cuộn' (Total Rolls) cho từng loại sợi.
    Dữ liệu trả về dạng:
    [
        {
            "material_id": 1,
            "material_name": "03300-PES-WEISS",
            "total_rolls": 348
        },
        ...
    ]
    """
    # Kiểm tra BOM tồn tại trước
    bom = db.query(BOMHeader).filter(BOMHeader.bom_id == bom_id).first()
    if not bom:
        raise HTTPException(status_code=404, detail="BOM not found")
        
    # Gọi Service tính toán
    summary = BOMService.get_bom_material_summary(db=db, bom_id=bom_id)
    return summary

# -------------------------------------------------------------------
# 5. CẬP NHẬT BOM (Tính toán lại toàn bộ)
# -------------------------------------------------------------------
@router.put("/{bom_id}", response_model=BOMHeaderResponse)
def update_bom(
    bom_id: int,
    bom_in: BOMHeaderUpdate,
    background_tasks: BackgroundTasks, # [THÊM]
    db: Session = Depends(get_db)
) -> Any:
    """
    Cập nhật thông tin BOM.
    
    - Nếu thay đổi `applicable_year`, hệ thống sẽ check trùng lặp.
    - Nếu gửi kèm `details`, hệ thống sẽ tính toán lại toàn bộ định mức.
    """
    try:
        updated_bom = BOMService.update_bom(db=db, bom_id=bom_id, bom_update=bom_in)
        # [THÊM] Phát tín hiệu làm mới danh sách BOM và có thể là chi tiết BOM đó
        background_tasks.add_task(ws_manager.broadcast, "REFRESH_BOMS")
        # Tuỳ chọn: Có thể bắn thêm ID để UI biết chính xác BOM nào vừa cập nhật
        # background_tasks.add_task(ws_manager.broadcast, f"UPDATE_BOM_{bom_id}")
        return updated_bom
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# -------------------------------------------------------------------
# 6. XÓA BOM
# -------------------------------------------------------------------
@router.delete("/{bom_id}", response_model=dict)
def delete_bom(
    bom_id: int,
    background_tasks: BackgroundTasks, # [THÊM]
    db: Session = Depends(get_db)
) -> Any:
    """
    Xóa cứng một BOM khỏi hệ thống.
    """
    success = BOMService.delete_bom(db=db, bom_id=bom_id)
    if not success:
        raise HTTPException(status_code=404, detail="BOM not found")
    
    # [THÊM] Phát tín hiệu làm mới danh sách BOM
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_BOMS")
    
    return {"message": "BOM deleted successfully", "bom_id": bom_id}

# -------------------------------------------------------------------
# 7. IMPORT EXCEL
# -------------------------------------------------------------------
@router.post("/import", status_code=200)
def import_bom_excel(
    background_tasks: BackgroundTasks,
    applicable_year: int = Form(..., description="Năm áp dụng cho toàn bộ BOM trong file"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
) -> Any:
    """
    Upload file Excel để tự động import và tính toán hàng loạt BOM.
    Hệ thống sẽ quét từng Sheet trong file Excel.
    """
    if not file.filename.endswith(('.xls', '.xlsx')):
        raise HTTPException(status_code=400, detail="Chỉ chấp nhận định dạng .xls hoặc .xlsx")
        
    result = BOMService.import_bom_from_excel(db, file, applicable_year)
    
    if result.get("status"):
        if result.get("success_count", 0) > 0:
            # Bắn tín hiệu làm mới giao diện
            background_tasks.add_task(ws_manager.broadcast, "REFRESH_BOMS")
        return result
    else:
        raise HTTPException(status_code=400, detail=result.get("message"))

