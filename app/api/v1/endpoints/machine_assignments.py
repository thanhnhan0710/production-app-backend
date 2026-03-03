from datetime import datetime
import pandas as pd

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import or_
from sqlalchemy.orm import Session
from typing import List, Optional

from app.api import deps
from app.models.machine import Machine
from app.models.product import Product
from app.schemas.machine_product_history_schema import MachineProductHistoryResponse, MachineProductAssign, MachineProductHistoryUpdate
from app.services import machine_product_history_service
from app.core.websockets import ws_manager
import io

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

# ==========================================
# [CẬP NHẬT] API LỊCH SỬ CÓ LỌC NGÀY & PHÂN TRANG
# ==========================================

@router.get("/history/all/global", response_model=List[MachineProductHistoryResponse])
def get_global_history(
    keyword: Optional[str] = None, 
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    skip: int = Query(0, ge=0), 
    limit: int = Query(50, le=500), 
    db: Session = Depends(deps.get_db)
):
    query = db.query(machine_product_history_service.MachineProductHistory)\
              .options(
                  machine_product_history_service.joinedload(machine_product_history_service.MachineProductHistory.product),
                  machine_product_history_service.joinedload(machine_product_history_service.MachineProductHistory.machine)
              )
    
    if keyword:
        query = query.join(Product).join(Machine).filter(
            or_(
                Product.item_code.ilike(f"%{keyword}%"),
                Machine.machine_name.ilike(f"%{keyword}%")
            )
        )
    
    if start_date:
        query = query.filter(machine_product_history_service.MachineProductHistory.start_time >= start_date)
    if end_date:
        query = query.filter(machine_product_history_service.MachineProductHistory.start_time <= end_date)
        
    return query.order_by(machine_product_history_service.MachineProductHistory.start_time.desc()).offset(skip).limit(limit).all()

@router.get("/{machine_id}/history", response_model=List[MachineProductHistoryResponse])
def get_machine_history(
    machine_id: int, 
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    skip: int = Query(0, ge=0), 
    limit: int = Query(50, le=500), 
    db: Session = Depends(deps.get_db)
):
    query = db.query(machine_product_history_service.MachineProductHistory)\
             .options(machine_product_history_service.joinedload(machine_product_history_service.MachineProductHistory.product))\
             .filter(machine_product_history_service.MachineProductHistory.machine_id == machine_id)
             
    if start_date:
        query = query.filter(machine_product_history_service.MachineProductHistory.start_time >= start_date)
    if end_date:
        query = query.filter(machine_product_history_service.MachineProductHistory.start_time <= end_date)

    return query.order_by(machine_product_history_service.MachineProductHistory.start_time.desc()).offset(skip).limit(limit).all()

# ==========================================
# [MỚI] API XUẤT EXCEL
# ==========================================
def _generate_excel_response(data: list, filename: str):
    df = pd.DataFrame(data)
    stream = io.BytesIO()
    with pd.ExcelWriter(stream, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='LichSu')
    stream.seek(0)
    return StreamingResponse(
        stream, 
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
        headers={"Content-Disposition": f"attachment; filename={filename}.xlsx"}
    )

@router.get("/export/global")
def export_global_history(
    keyword: Optional[str] = None, 
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(deps.get_db)
):
    # Lấy toàn bộ không limit để xuất Excel
    records = get_global_history(keyword, start_date, end_date, skip=0, limit=10000, db=db)
    
    export_data = []
    for r in records:
        export_data.append({
            "Tên Máy": r.machine.machine_name if r.machine else f"ID {r.machine_id}",
            "Mã Hàng": r.product.item_code if r.product else "N/A",
            "Ghi chú SP": r.product.note if r.product else "",
            "Thời gian Bắt đầu": r.start_time.strftime("%Y-%m-%d %H:%M:%S") if r.start_time else "",
            "Thời gian Kết thúc": r.end_time.strftime("%Y-%m-%d %H:%M:%S") if r.end_time else "ĐANG CHẠY",
            "Ghi chú": r.notes or ""
        })
        
    return _generate_excel_response(export_data, "LichSu_ToanXuong")

@router.get("/export/{machine_id}")
def export_single_machine_history(
    machine_id: int,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(deps.get_db)
):
    records = get_machine_history(machine_id, start_date, end_date, skip=0, limit=10000, db=db)
    
    export_data = []
    for r in records:
        export_data.append({
            "Mã Hàng": r.product.item_code if r.product else "N/A",
            "Thời gian Bắt đầu": r.start_time.strftime("%Y-%m-%d %H:%M:%S") if r.start_time else "",
            "Thời gian Kết thúc": r.end_time.strftime("%Y-%m-%d %H:%M:%S") if r.end_time else "ĐANG CHẠY",
            "Ghi chú": r.notes or ""
        })
        
    return _generate_excel_response(export_data, f"LichSu_May_{machine_id}")
# 2. API lấy danh sách các máy ĐANG CHẠY (để hiển thị lên Dashboard)
@router.get("/status/active-all", response_model=List[MachineProductHistoryResponse])
def get_all_active_assignments(db: Session = Depends(deps.get_db)):
    return db.query(machine_product_history_service.MachineProductHistory)\
             .options(machine_product_history_service.joinedload(machine_product_history_service.MachineProductHistory.product))\
             .filter(machine_product_history_service.MachineProductHistory.end_time == None).all()