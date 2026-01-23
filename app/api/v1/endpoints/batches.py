from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.api import deps
from app.schemas.batch_schema import BatchResponse, BatchCreate, BatchUpdate, BatchQCStatus
from app.services.batch_service import BatchService

router = APIRouter()

# 1. Lấy danh sách (Có bổ sung filter receipt_detail_id)
@router.get("/", response_model=List[BatchResponse])
def read_batches(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    supplier_batch: Optional[str] = None,
    material_id: Optional[int] = None,
    qc_status: Optional[BatchQCStatus] = None,
    # [MỚI - Optional] Thêm dòng này nếu bạn muốn lọc theo chi tiết phiếu nhập
    # receipt_detail_id: Optional[int] = None, 
    db: Session = Depends(deps.get_db)
):
    service = BatchService(db)
    
    # Lưu ý: Nếu thêm tham số receipt_detail_id ở trên, 
    # bạn cần cập nhật thêm tham số này vào hàm service.get_multi() tương ứng.
    # Hiện tại code dưới chạy theo service cũ vẫn OK.
    return service.get_multi(
        skip=skip, 
        limit=limit, 
        search=search, 
        material_id=material_id, 
        qc_status=qc_status, 
        supplier_batch=supplier_batch
    )

# 2. Tạo mới (Tự động nhận receipt_detail_id từ Schema)
@router.post("/", response_model=BatchResponse)
def create_batch(batch_in: BatchCreate, db: Session = Depends(deps.get_db)):
    service = BatchService(db)
    return service.create(batch_in)

# 3. Xem chi tiết
@router.get("/{batch_id}", response_model=BatchResponse)
def read_batch(batch_id: int, db: Session = Depends(deps.get_db)):
    service = BatchService(db)
    batch = service.get(batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Không tìm thấy lô hàng")
    return batch

# 4. Cập nhật
@router.put("/{batch_id}", response_model=BatchResponse)
def update_batch(
    batch_id: int, 
    batch_in: BatchUpdate, 
    db: Session = Depends(deps.get_db)
):
    service = BatchService(db)
    batch = service.get(batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Không tìm thấy lô hàng")
    return service.update(db_obj=batch, obj_in=batch_in)

# 5. Cập nhật trạng thái QC
@router.put("/{batch_id}/qc-status", response_model=BatchResponse)
def update_batch_qc_status(
    batch_id: int, 
    status: BatchQCStatus, 
    note: Optional[str] = None,
    db: Session = Depends(deps.get_db)
):
    service = BatchService(db)
    # Service tự check lỗi 404
    return service.update_qc_status(batch_id=batch_id, status=status, note=note)

# 6. Xóa
@router.delete("/{batch_id}")
def delete_batch(batch_id: int, db: Session = Depends(deps.get_db)):
    service = BatchService(db)
    service.delete(batch_id)
    return {"message": "Xóa lô hàng thành công"}