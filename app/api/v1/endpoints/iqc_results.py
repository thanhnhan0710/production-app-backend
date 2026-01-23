from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.api import deps
from app.schemas.iqc_result_schema import (
    IQCResultCreate,
    IQCResultUpdate,
    IQCResultResponse
)
from app.services.iqc_service import IQCService

router = APIRouter()

@router.get("/", response_model=List[IQCResultResponse])
def read_iqc_results(
    skip: int = 0,
    limit: int = 100,
    batch_id: Optional[int] = Query(None, description="Lọc theo ID lô hàng"),
    db: Session = Depends(deps.get_db)
):
    """
    Lấy danh sách kết quả kiểm tra IQC.
    """
    service = IQCService(db)
    if batch_id:
        return service.get_by_batch(batch_id)
    return service.get_multi(skip=skip, limit=limit)

@router.post("/", response_model=IQCResultResponse)
def create_iqc_result(
    item_in: IQCResultCreate,
    db: Session = Depends(deps.get_db)
):
    """
    Tạo phiếu kết quả kiểm tra chất lượng.
    Lưu ý: Hành động này sẽ tự động cập nhật trạng thái của Lô hàng (Batch) thành Pass/Fail.
    """
    service = IQCService(db)
    return service.create(obj_in=item_in)

@router.get("/{test_id}", response_model=IQCResultResponse)
def read_iqc_result(
    test_id: int,
    db: Session = Depends(deps.get_db)
):
    """Lấy chi tiết một phiếu kiểm tra."""
    service = IQCService(db)
    item = service.get(test_id)
    if not item:
        raise HTTPException(status_code=404, detail="Kết quả kiểm tra không tồn tại.")
    return item

@router.put("/{test_id}", response_model=IQCResultResponse)
def update_iqc_result(
    test_id: int,
    item_in: IQCResultUpdate,
    db: Session = Depends(deps.get_db)
):
    """
    Cập nhật kết quả kiểm tra.
    Nếu kết quả thay đổi (Pass -> Fail hoặc ngược lại), trạng thái Lô hàng cũng sẽ được cập nhật theo.
    """
    service = IQCService(db)
    item = service.get(test_id)
    if not item:
        raise HTTPException(status_code=404, detail="Kết quả kiểm tra không tồn tại.")
    return service.update(db_obj=item, obj_in=item_in)