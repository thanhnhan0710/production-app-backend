from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional

from app.api import deps
from app.core.websockets import ws_manager

from app.schemas.material_receipt_schema import MaterialReceiptCreate, MaterialReceiptUpdate, MaterialReceiptResponse
from app.services.material_receipt_service import material_receipt_service

router = APIRouter()

@router.get("/count", response_model=int)
def get_receipt_count(db: Session = Depends(deps.get_db)):
    """Lấy tổng số lượng Phiếu nhập kho"""
    return material_receipt_service.count_receipts(db)

@router.get("/", response_model=List[MaterialReceiptResponse])
def read_receipts(
    skip: int = 0, 
    limit: int = 100, 
    search: Optional[str] = None,
    status: Optional[str] = None,
    warehouse_id: Optional[int] = None,
    db: Session = Depends(deps.get_db)
):
    """Lấy danh sách Phiếu nhập kho (Hỗ trợ lọc theo trạng thái, kho)"""
    return material_receipt_service.get_receipts(
        db, skip=skip, limit=limit, search=search, status=status, warehouse_id=warehouse_id
    )

@router.get("/{receipt_id}", response_model=MaterialReceiptResponse)
def read_receipt(receipt_id: int, db: Session = Depends(deps.get_db)):
    """Lấy chi tiết 1 Phiếu nhập kho"""
    receipt = material_receipt_service.get_receipt(db, receipt_id)
    if not receipt:
        raise HTTPException(status_code=404, detail="Không tìm thấy Phiếu nhập kho.")
    return receipt

@router.post("/", response_model=MaterialReceiptResponse)
def create_receipt(
    receipt_in: MaterialReceiptCreate, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db)
):
    """
    Thêm mới Phiếu nhập kho. 
    Nếu status='Completed', hệ thống tự động sinh Lô và cộng Tồn kho.
    """
    new_receipt = material_receipt_service.create_receipt(db, receipt_in)
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_MATERIAL_RECEIPTS")
    return new_receipt

@router.put("/{receipt_id}", response_model=MaterialReceiptResponse)
def update_receipt(
    receipt_id: int, 
    receipt_in: MaterialReceiptUpdate, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db)
):
    """
    Cập nhật Phiếu nhập kho. 
    Nếu chuyển status sang 'Completed', hệ thống sẽ tự sinh Lô và cộng Tồn kho.
    """
    updated_receipt = material_receipt_service.update_receipt(db, receipt_id, receipt_in)
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_MATERIAL_RECEIPTS")
    # Cập nhật thêm tồn kho/lô cho client nếu duyệt phiếu
    if receipt_in.status == "Completed":
        background_tasks.add_task(ws_manager.broadcast, "REFRESH_MATERIAL_BATCHES")
        background_tasks.add_task(ws_manager.broadcast, "REFRESH_MATERIAL_INVENTORIES")
    return updated_receipt

@router.delete("/{receipt_id}")
def delete_receipt(
    receipt_id: int, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db)
):
    """Xóa Phiếu nhập kho (Chỉ phiếu Draft)"""
    result = material_receipt_service.delete_receipt(db, receipt_id)
    if not result:
        raise HTTPException(status_code=404, detail="Không tìm thấy Phiếu nhập kho hoặc Phiếu đã hoàn thành không thể xóa.")
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_MATERIAL_RECEIPTS")
    return {"message": "Đã xóa Phiếu nhập kho thành công"}