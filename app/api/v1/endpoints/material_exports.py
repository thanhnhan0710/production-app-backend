from fastapi import APIRouter, Depends, Query, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from datetime import date, datetime
import pandas as pd
import io

from app.api import deps
from app.schemas.material_export_schema import (
    MaterialExportCreate, 
    MaterialExportUpdate, 
    MaterialExportResponse
)
from app.services.material_export_service import MaterialExportService
from app.core.websockets import ws_manager

router = APIRouter()

@router.get("/next-number", response_model=Dict[str, str])
def get_next_export_number(db: Session = Depends(deps.get_db)):
    service = MaterialExportService(db)
    new_code = service.generate_next_export_code()
    return {"export_code": new_code}

# ==========================================
# [MỚI] ENDPOINT XUẤT FILE EXCEL
# ==========================================
@router.get("/export-excel")
def export_excel(
    search: Optional[str] = None,
    warehouse_id: Optional[int] = None,
    exporter_id: Optional[int] = None,
    receiver_id: Optional[int] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    db: Session = Depends(deps.get_db)
):
    service = MaterialExportService(db)
    # Kéo toàn bộ dữ liệu dựa theo bộ lọc
    records = service.get_all_for_export_excel(
        search=search,
        warehouse_id=warehouse_id,
        exporter_id=exporter_id,
        receiver_id=receiver_id,
        from_date=from_date,
        to_date=to_date
    )

    # Chuyển đổi dữ liệu thành dạng List of Dictionary (Bảng phẳng)
    data = []
    for r in records:
        # Nếu phiếu trống không có detail
        if not r.details:
            data.append({
                "Mã phiếu xuất": r.export_code,
                "Ngày xuất": r.export_date.strftime("%d/%m/%Y") if r.export_date else "",
                "Kho xuất": r.warehouse.name if r.warehouse else "",
                "Người xuất": r.exporter.full_name if r.exporter else "",
                "Người nhận": r.receiver.full_name if r.receiver else "",
                "Mã Vật Tư": "", "Tên Vật Tư": "", "Mã Lô": "",
                "Khối lượng (Kg)": 0, "Số cuộn": 0, "Số Pallet": 0,
                "Loại Sợi": "", "Máy nhận (Loom)": "", "Mã SP dệt": "",
                "Ghi chú phiếu": r.note or "",
                "Ghi chú dòng": ""
            })
            continue

        # Duyệt qua từng dòng detail của phiếu
        for d in r.details:
            loom_machine = f"{d.loom.machine.machine_name} (Line {d.loom.line_number})" if d.loom and d.loom.machine else ""
            loom_product = d.loom.product.item_code if d.loom and d.loom.product else ""

            data.append({
                "Mã phiếu xuất": r.export_code,
                "Ngày xuất": r.export_date.strftime("%d/%m/%Y") if r.export_date else "",
                "Kho xuất": r.warehouse.warehouse_name if r.warehouse else "",
                "Người xuất": r.exporter.full_name if r.exporter else "",
                "Người nhận": r.receiver.full_name if r.receiver else "",
                "Mã Vật Tư": d.material.material_code if d.material else "",
                "Tên Vật Tư": d.material.material_name if d.material else "",
                "Mã Lô": d.batch.batch_code if d.batch else "",
                "Khối lượng (Kg)": d.quantity_kg,
                "Số cuộn": d.quantity_cones,
                "Số Pallet": d.number_of_pallets,
                "Loại Sợi": d.component_type or "",
                "Máy nhận (Loom)": loom_machine,
                "Mã SP dệt": loom_product,
                "Ghi chú phiếu": r.note or "",
                "Ghi chú dòng": d.note or ""
            })

    # Tạo file Excel bằng Pandas
    df = pd.DataFrame(data)
    stream = io.BytesIO()
    with pd.ExcelWriter(stream, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='XuatKho')
    
    stream.seek(0)
    
    filename = f"DanhSachXuatKho_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    return StreamingResponse(
        stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

# ==========================================
# CÁC ENDPOINT CŨ GIỮ NGUYÊN
# ==========================================
@router.get("/", response_model=List[MaterialExportResponse])
def read_exports(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=500),
    search: Optional[str] = None,
    warehouse_id: Optional[int] = None,
    exporter_id: Optional[int] = None,
    receiver_id: Optional[int] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    db: Session = Depends(deps.get_db)
):
    service = MaterialExportService(db)
    return service.get_multi(
        skip=skip, 
        limit=limit, 
        search=search,
        warehouse_id=warehouse_id,
        exporter_id=exporter_id,
        receiver_id=receiver_id,
        from_date=from_date,
        to_date=to_date
    )

@router.post("/", response_model=MaterialExportResponse)
def create_export(
    export_in: MaterialExportCreate, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db)
):
    service = MaterialExportService(db)
    new_export = service.create_export(export_in)
    
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_MATERIAL_EXPORTS")
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_MATERIAL_INVENTORIES")
    return new_export

@router.get("/active-batches-on-machine")
def get_active_batches_on_machine(
    machine_id: int,
    product_id: int,
    db: Session = Depends(deps.get_db)
):
    service = MaterialExportService(db)
    return service.get_active_batches_on_machine(machine_id, product_id)

@router.get("/{id}", response_model=MaterialExportResponse)
def read_export_detail(id: int, db: Session = Depends(deps.get_db)):
    service = MaterialExportService(db)
    item = service.get(id)
    if not item:
        raise HTTPException(status_code=404, detail="Phiếu xuất không tồn tại")
    return item

@router.put("/{id}", response_model=MaterialExportResponse)
def update_export(
    id: int, 
    export_in: MaterialExportUpdate, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db)
):
    service = MaterialExportService(db)
    updated_export = service.update(id, export_in)
    
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_MATERIAL_EXPORTS")
    return updated_export

@router.delete("/{id}")
def delete_export(
    id: int, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db)
):
    service = MaterialExportService(db)
    result = service.delete(id)
    
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_MATERIAL_EXPORTS")
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_MATERIAL_INVENTORIES")
    return result