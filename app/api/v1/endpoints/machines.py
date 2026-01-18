import os
import shutil
import uuid
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from sqlalchemy.orm import Session
from typing import List, Optional

from app.api import deps
from app.schemas.machine_schema import (
    MachineResponse,
    MachineCreate,
    MachineUpdate
)
from app.services import machine_service

router = APIRouter()

# --- CẤU HÌNH ĐƯỜNG DẪN (Đồng bộ với upload.py) ---
BASE_STATIC_DIR = "static/uploads"
MACHINE_LOG_DIR = f"{BASE_STATIC_DIR}/machine_logs"

# =========================
# GET LIST
# =========================
@router.get("/", response_model=List[MachineResponse])
def read_machines(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db)
):
    return machine_service.get_machines(db, skip=skip, limit=limit)


# =========================
# CREATE
# =========================
@router.post("/", response_model=MachineResponse)
def create_machine(
    machine: MachineCreate,
    db: Session = Depends(deps.get_db)
):
    return machine_service.create_machine(db, machine)


# =========================
# UPDATE
# =========================
@router.put("/{machine_id}", response_model=MachineResponse)
def update_machine(
    machine_id: int,
    machine: MachineUpdate,
    db: Session = Depends(deps.get_db)
):
    updated_machine = machine_service.update_machine(
        db, machine_id, machine
    )
    if not updated_machine:
        raise HTTPException(status_code=404, detail="Machine not found")
    return updated_machine


# =========================
# DELETE
# =========================
@router.delete("/{machine_id}")
def delete_machine(
    machine_id: int,
    db: Session = Depends(deps.get_db)
):
    success = machine_service.delete_machine(db, machine_id)
    if not success:
        raise HTTPException(status_code=404, detail="Machine not found")
    return {"message": "Deleted successfully"}


# =========================
# SEARCH
# =========================
@router.get("/search", response_model=List[MachineResponse])
def search_machines(
    keyword: str | None = None,
    status: str | None = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db)
):
    return machine_service.search_machines(
        db=db,
        keyword=keyword,
        status=status,
        skip=skip,
        limit=limit
    )

# =========================
# UPDATE STATUS & LOG WITH IMAGE
# =========================
@router.put("/{machine_id}/status", response_model=MachineResponse)
def update_machine_status_endpoint(
    machine_id: int,
    # Sử dụng Form và File để nhận dữ liệu Multipart
    status: str = Form(...),
    reason: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None), 
    db: Session = Depends(deps.get_db)
):
    image_url_path = None

    # 1. Xử lý lưu file nếu có ảnh gửi lên
    if image:
        try:
            # Tạo thư mục nếu chưa tồn tại (Dùng MACHINE_LOG_DIR đã định nghĩa ở trên)
            if not os.path.exists(MACHINE_LOG_DIR):
                os.makedirs(MACHINE_LOG_DIR)
            
            # Tạo tên file duy nhất (UUID) để tránh trùng lặp
            file_extension = os.path.splitext(image.filename)[1]
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            
            file_path = f"{MACHINE_LOG_DIR}/{unique_filename}"
            
            # Lưu file vào ổ cứng
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(image.file, buffer)
            
            # Tạo đường dẫn URL để lưu vào DB (bắt đầu bằng dấu / để thành đường dẫn tương đối)
            # Ví dụ: /static/uploads/machine_logs/abc-xyz.jpg
            image_url_path = f"/{file_path}"
            
        except Exception as e:
            print(f"Lỗi lưu file: {e}")
            # Tùy chọn: Có thể raise lỗi nếu bắt buộc phải có ảnh, hoặc bỏ qua để log không ảnh
            # raise HTTPException(status_code=500, detail="Could not save image file")

    # 2. Gọi Service update
    updated_machine = machine_service.update_machine_status(
        db, 
        machine_id, 
        status, 
        reason, 
        image_url_path # Truyền đường dẫn ảnh vừa lưu (hoặc None)
    )
    
    if not updated_machine:
        raise HTTPException(status_code=404, detail="Machine not found")
        
    return updated_machine