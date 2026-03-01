from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy import or_
from sqlalchemy.orm import Session
from typing import List

from app.api import deps
from app.models.machine import Machine
from app.models.product import Product
from app.schemas.machine_product_history_schema import MachineProductHistoryResponse, MachineProductAssign, MachineProductHistoryUpdate
from app.services import machine_product_history_service
from app.core.websockets import ws_manager

router = APIRouter()

@router.post("/{machine_id}/assign", response_model=MachineProductHistoryResponse)
def assign_product(machine_id: int, data: MachineProductAssign, background_tasks: BackgroundTasks, db: Session = Depends(deps.get_db)):
    try:
        result = machine_product_history_service.assign_product_to_machine(db, machine_id, data)
        background_tasks.add_task(ws_manager.broadcast, f"REFRESH_MACHINE_{machine_id}_PRODUCT")
        background_tasks.add_task(ws_manager.broadcast, "REFRESH_MACHINES")
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{machine_id}/stop")
def stop_product(machine_id: int, background_tasks: BackgroundTasks, db: Session = Depends(deps.get_db)):
    result = machine_product_history_service.stop_machine_production(db, machine_id)
    if not result:
        return {"message": "Máy hiện không chạy sản phẩm nào."}
    background_tasks.add_task(ws_manager.broadcast, f"REFRESH_MACHINE_{machine_id}_PRODUCT")
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_MACHINES")
    return {"message": "Đã dừng sản xuất sản phẩm hiện tại."}

@router.get("/{machine_id}/current", response_model=MachineProductHistoryResponse)
def get_current_product(machine_id: int, db: Session = Depends(deps.get_db)):
    result = machine_product_history_service.get_current_product_of_machine(db, machine_id)
    if not result:
        raise HTTPException(status_code=404, detail="Máy đang trống, không chạy sản phẩm nào")
    return result

@router.get("/{machine_id}/history", response_model=List[MachineProductHistoryResponse])
def get_history(machine_id: int, skip: int = 0, limit: int = 50, db: Session = Depends(deps.get_db)):
    return machine_product_history_service.get_machine_history(db, machine_id, skip, limit)

# ==========================================
# [MỚI] API ENDPOINTS CHO SỬA, XÓA, TÌM KIẾM
# ==========================================

@router.get("/{machine_id}/history/search", response_model=List[MachineProductHistoryResponse])
def search_history(machine_id: int, keyword: str, skip: int = 0, limit: int = 50, db: Session = Depends(deps.get_db)):
    return machine_product_history_service.search_machine_history(db, machine_id, keyword, skip, limit)

@router.put("/history/{history_id}", response_model=MachineProductHistoryResponse)
def update_history(history_id: int, data: MachineProductHistoryUpdate, background_tasks: BackgroundTasks, db: Session = Depends(deps.get_db)):
    result = machine_product_history_service.update_history_record(db, history_id, data)
    if not result:
        raise HTTPException(status_code=404, detail="Không tìm thấy bản ghi lịch sử này")
    # Thông báo refresh cho machine tương ứng của bản ghi này
    background_tasks.add_task(ws_manager.broadcast, f"REFRESH_MACHINE_{result.machine_id}_PRODUCT")
    return result

@router.delete("/history/{history_id}")
def delete_history(history_id: int, background_tasks: BackgroundTasks, db: Session = Depends(deps.get_db)):
    # Phải lấy machine_id trước khi xóa để bắn socket
    record = db.query(machine_product_history_service.MachineProductHistory).filter(machine_product_history_service.MachineProductHistory.id == history_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Không tìm thấy bản ghi lịch sử này")
    
    machine_id = record.machine_id
    success = machine_product_history_service.delete_history_record(db, history_id)
    
    background_tasks.add_task(ws_manager.broadcast, f"REFRESH_MACHINE_{machine_id}_PRODUCT")
    return {"message": "Đã xóa bản ghi lịch sử thành công"}

# 1. API lấy toàn bộ lịch sử của TẤT CẢ các máy (Global History)
@router.get("/history/all/global", response_model=List[MachineProductHistoryResponse])
def get_global_history(keyword: str = None, skip: int = 0, limit: int = 100, db: Session = Depends(deps.get_db)):
    query = db.query(machine_product_history_service.MachineProductHistory)\
              .options(
                  machine_product_history_service.joinedload(machine_product_history_service.MachineProductHistory.product),
                  machine_product_history_service.joinedload(machine_product_history_service.MachineProductHistory.machine)
              )
    
    if keyword:
        # Cho phép tìm theo tên máy HOẶC mã sản phẩm
        query = query.join(Product).join(Machine).filter(
            or_(
                Product.item_code.ilike(f"%{keyword}%"),
                Machine.machine_name.ilike(f"%{keyword}%")
            )
        )
    return query.order_by(machine_product_history_service.MachineProductHistory.start_time.desc()).offset(skip).limit(limit).all()

# 2. API lấy danh sách các máy ĐANG CHẠY (để hiển thị lên Dashboard)
@router.get("/status/active-all", response_model=List[MachineProductHistoryResponse])
def get_all_active_assignments(db: Session = Depends(deps.get_db)):
    return db.query(machine_product_history_service.MachineProductHistory)\
             .options(machine_product_history_service.joinedload(machine_product_history_service.MachineProductHistory.product))\
             .filter(machine_product_history_service.MachineProductHistory.end_time == None).all()