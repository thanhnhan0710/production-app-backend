from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.api import deps
from app.core.websockets import ws_manager
from app.schemas.material_inventory_schema import InventoryInitStock, MaterialInventoryCreate, MaterialInventoryUpdate, MaterialInventoryResponse
from app.services.material_inventory_service import material_inventory_service

router = APIRouter()

@router.get("/count", response_model=int)
def get_inventory_count(db: Session = Depends(deps.get_db)):
    """Lấy tổng số lượng bản ghi Tồn kho"""
    return material_inventory_service.count_inventories(db)

# ==========================================
# [QUAN TRỌNG] API XUẤT EXCEL (Phải đặt TRƯỚC API /{inventory_id})
# ==========================================
@router.get("/export-excel")
def export_inventories_to_excel(
    warehouse_id: Optional[int] = None,
    material_id: Optional[int] = None,
    is_low_stock: bool = False, # [MỚI]
    db: Session = Depends(deps.get_db)
):
    """Xuất Tồn kho thực tế ra file Excel"""
    file_stream = material_inventory_service.export_excel(
        db, warehouse_id=warehouse_id, material_id=material_id
    )
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"TonKhoNVL_{timestamp}.xlsx"
    
    return StreamingResponse(
        file_stream, 
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={file_name}"}
    )

@router.get("/", response_model=List[MaterialInventoryResponse])
def read_inventories(
    skip: int = 0, 
    limit: int = 100, 
    search: Optional[str] = None,
    warehouse_id: Optional[int] = None,
    material_id: Optional[int] = None,
    is_low_stock: bool = False, # [MỚI]
    db: Session = Depends(deps.get_db)
):
    return material_inventory_service.get_inventories(
        db, skip=skip, limit=limit, warehouse_id=warehouse_id, material_id=material_id, is_low_stock=is_low_stock
    )

@router.get("/{inventory_id}", response_model=MaterialInventoryResponse)
def read_inventory(inventory_id: int, db: Session = Depends(deps.get_db)):
    """Lấy chi tiết 1 bản ghi Tồn kho"""
    inventory = material_inventory_service.get_inventory(db, inventory_id)
    if not inventory:
        raise HTTPException(status_code=404, detail="Không tìm thấy bản ghi Tồn kho.")
    return inventory

@router.post("/init-stock", response_model=MaterialInventoryResponse)
def init_inventory_stock(
    init_data: InventoryInitStock, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db)
):
    """Khởi tạo Tồn kho đầu kỳ (Tự động sinh Lô và tạo tồn kho)"""
    new_inv = material_inventory_service.init_stock(db, init_data)
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_MATERIAL_INVENTORIES")
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_MATERIAL_BATCHES")
    return new_inv

@router.post("/", response_model=MaterialInventoryResponse)
def create_inventory(
    inventory_in: MaterialInventoryCreate, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db)
):
    """Khởi tạo Tồn kho đầu kỳ thủ công"""
    new_inventory = material_inventory_service.create_inventory(db, inventory_in)
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_MATERIAL_INVENTORIES")
    return new_inventory

@router.put("/{inventory_id}", response_model=MaterialInventoryResponse)
def update_inventory(
    inventory_id: int, 
    inventory_in: MaterialInventoryUpdate, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db)
):
    """Điều chỉnh Tồn kho thủ công (Sửa lệch kiểm kê, cập nhật Vị trí...)"""
    updated_inventory = material_inventory_service.update_inventory(db, inventory_id, inventory_in)
    if not updated_inventory:
        raise HTTPException(status_code=404, detail="Không tìm thấy bản ghi Tồn kho để cập nhật.")
    
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_MATERIAL_INVENTORIES")
    return updated_inventory

@router.delete("/{inventory_id}")
def delete_inventory(
    inventory_id: int, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db)
):
    """Xóa một bản ghi Tồn kho"""
    db_obj = material_inventory_service.get_inventory(db, inventory_id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Không tìm thấy bản ghi Tồn kho.")
    
    db.delete(db_obj)
    db.commit()
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_MATERIAL_INVENTORIES")
    return {"message": "Đã xóa tồn kho thành công"}