import os
import shutil
import uuid
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form, BackgroundTasks, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional

from app.schemas.machine_log_schema import MachineLogResponse
from app.api import deps
from app.schemas.machine_schema import MachineResponse, MachineCreate, MachineUpdate
from app.services import machine_service
from app.core.websockets import ws_manager

router = APIRouter()

BASE_STATIC_DIR = "static/uploads"
MACHINE_LOG_DIR = f"{BASE_STATIC_DIR}/machine_logs"

@router.get("/", response_model=List[MachineResponse])
def read_machines(skip: int = 0, limit: int = 100, db: Session = Depends(deps.get_db)):
    return machine_service.get_machines(db, skip=skip, limit=limit)

# =============================================================================
# [API MỚI]: Lấy danh sách trạng thái của toàn bộ các Line đang hoạt động
# =============================================================================
@router.get("/lines/active-statuses")
def get_active_lines_statuses(db: Session = Depends(deps.get_db)):
    return machine_service.get_active_line_statuses(db)

@router.post("/", response_model=MachineResponse)
def create_machine(machine: MachineCreate, background_tasks: BackgroundTasks, db: Session = Depends(deps.get_db)):
    new_machine = machine_service.create_machine(db, machine)
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_MACHINES")
    return new_machine

@router.put("/{machine_id}", response_model=MachineResponse)
def update_machine(machine_id: int, machine: MachineUpdate, background_tasks: BackgroundTasks, db: Session = Depends(deps.get_db)):
    updated_machine = machine_service.update_machine(db, machine_id, machine)
    if not updated_machine: raise HTTPException(status_code=404, detail="Machine not found")
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_MACHINES")
    return updated_machine

@router.delete("/{machine_id}")
def delete_machine(machine_id: int, background_tasks: BackgroundTasks, db: Session = Depends(deps.get_db)):
    success = machine_service.delete_machine(db, machine_id)
    if not success: raise HTTPException(status_code=404, detail="Machine not found")
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_MACHINES")
    return {"message": "Deleted successfully"}

@router.get("/search", response_model=List[MachineResponse])
def search_machines(
    keyword: str | None = None,
    status_id: int | None = None, 
    area_id: int | None = None,   
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db)
):
    return machine_service.search_machines(db=db, keyword=keyword, status_id=status_id, area_id=area_id, skip=skip, limit=limit)

@router.patch("/{machine_id}/status", response_model=MachineResponse)
@router.put("/{machine_id}/status", response_model=MachineResponse)
async def update_machine_status_endpoint(
    machine_id: int, 
    request: Request,
    background_tasks: BackgroundTasks, 
    db: Session = Depends(deps.get_db)
):
    content_type = request.headers.get("content-type", "")
    
    status = None
    reason = None
    raw_lines = None # Dùng một biến chung để nhận dữ liệu lines thô
    image_url_path = None
    
    # Nếu App gửi lên là JSON (Thường xảy ra khi không đính kèm ảnh)
    if "application/json" in content_type:
        body = await request.json()
        status = body.get("status")
        reason = body.get("reason")
        raw_lines = body.get("lines") 
    else:
        # Nếu App gửi lên là FormData (Thường xảy ra khi có đính kèm ảnh)
        form = await request.form()
        status = form.get("status")
        reason = form.get("reason")
        raw_lines = form.get("lines") 
        image = form.get("image")
        
        # Xử lý lưu file ảnh nếu có
        if image and hasattr(image, "filename") and image.filename:
            try:
                if not os.path.exists(MACHINE_LOG_DIR): os.makedirs(MACHINE_LOG_DIR)
                file_extension = os.path.splitext(image.filename)[1]
                unique_filename = f"{uuid.uuid4()}{file_extension}"
                file_path = f"{MACHINE_LOG_DIR}/{unique_filename}"
                
                content = await image.read()
                with open(file_path, "wb") as buffer: 
                    buffer.write(content)
                image_url_path = f"/{file_path}"
            except Exception as e: print(f"Lỗi lưu file: {e}")

    if not status:
        raise HTTPException(status_code=422, detail="Trường 'status' là bắt buộc trong body hoặc form-data.")

    # Đảm bảo status là chuỗi (string)
    if isinstance(status, int):
        status = str(status)

    # [ĐÃ SỬA]: Xử lý danh sách lines thông minh hơn
    lines_list = []
    if raw_lines is not None:
        if isinstance(raw_lines, list):
            # Nếu Flutter gửi JSON mảng [1, 2]
            lines_list = [int(x) for x in raw_lines]
        elif isinstance(raw_lines, str) and raw_lines.strip() != "":
             # Nếu Flutter gửi FormData chuỗi "1,2"
             try:
                 lines_list = [int(x.strip()) for x in raw_lines.split(",") if x.strip()]
             except ValueError:
                 pass # Bỏ qua nếu có lỗi parse int

    updated_machine = machine_service.update_machine_status(db, machine_id, status, reason, image_url_path, lines_list)
    if not updated_machine: raise HTTPException(status_code=404, detail="Machine not found")
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_MACHINES")
    return updated_machine

@router.get("/{machine_id}/history", response_model=List[MachineLogResponse])
def read_machine_history(machine_id: int, limit: int = 100, db: Session = Depends(deps.get_db)):
    history_logs = machine_service.get_machine_history(db, machine_id=machine_id, limit=limit)
    return history_logs if history_logs else []

@router.post("/import", status_code=200)
def import_excel(background_tasks: BackgroundTasks, file: UploadFile = File(...), db: Session = Depends(deps.get_db)):
    if not file.filename.endswith(('.xls', '.xlsx')): raise HTTPException(status_code=400, detail="Chỉ chấp nhận định dạng .xls hoặc .xlsx")
    result = machine_service.import_machines_from_excel(db, file)
    if result.get("status"):
        if result.get("success_count", 0) > 0:
            background_tasks.add_task(ws_manager.broadcast, "REFRESH_MACHINES")
            background_tasks.add_task(ws_manager.broadcast, "REFRESH_AREAS") # Báo cho UI tải lại danh sách khu vực
        return result
    else: raise HTTPException(status_code=400, detail=result.get("message"))

@router.get("/export", status_code=200)
def export_excel(db: Session = Depends(deps.get_db)):
    output = machine_service.export_machines_to_excel(db)
    headers = {'Content-Disposition': 'attachment; filename="Machines.xlsx"'}
    return StreamingResponse(output, headers=headers, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')