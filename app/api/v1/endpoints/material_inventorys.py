from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional

from app.api import deps
from app.core.websockets import ws_manager

from app.schemas.material_inventory_schema import MaterialInventoryCreate, MaterialInventoryUpdate, MaterialInventoryResponse
from app.services.material_inventory_service import material_inventory_service

router = APIRouter()

@router.get("/count", response_model=int)
def get_inventory_count(db: Session = Depends(deps.get_db)):
    """Lấy tổng số lượng bản ghi Tồn kho"""
    return material_inventory_service.count_inventories(db)

@router.get("/", response_model=List[MaterialInventoryResponse])
def read_inventories(
    skip: int = 0, 
    limit: int = 100, 
    warehouse_id: Optional[int] = None,
    material_id: Optional[int] = None,
    db: Session = Depends(deps.get_db)
):
    """Lấy danh sách Tồn kho (Khả dụng)"""
    return material_inventory_service.get_inventories(
        db, skip=skip, limit=limit, warehouse_id=warehouse_id, material_id=material_id
    )

@router.get("/{inventory_id}", response_model=MaterialInventoryResponse)
def read_inventory(inventory_id: int, db: Session = Depends(deps.get_db)):
    """Lấy chi tiết 1 bản ghi Tồn kho"""
    inventory = material_inventory_service.get_inventory(db, inventory_id)
    if not inventory:
        raise HTTPException(status_code=404, detail="Không tìm thấy bản ghi Tồn kho.")
    return inventory

# Tồn kho thường không POST thủ công mà do Nhập/Xuất kho tạo ra, 
# nhưng nếu cần khởi tạo tồn kho đầu kỳ, có thể giữ API này
@router.post("/", response_model=MaterialInventoryResponse)
def create_inventory(
    inventory_in: MaterialInventoryCreate, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db)
):
    """Khởi tạo Tồn kho đầu kỳ"""
    # Bạn cần bổ sung hàm create_inventory trong Service nếu muốn dùng API này
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
    """Điều chỉnh Tồn kho thủ công (Sửa lệch kiểm kê, giữ chỗ...)"""
    updated_inventory = material_inventory_service.update_inventory(db, inventory_id, inventory_in)
    if not updated_inventory:
        raise HTTPException(status_code=404, detail="Không tìm thấy bản ghi Tồn kho để cập nhật.")
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_MATERIAL_INVENTORIES")
    return updated_inventory