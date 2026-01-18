import os
import shutil
import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException

router = APIRouter()

# --- CẤU HÌNH ĐƯỜNG DẪN ---
# Lưu ý: Dùng dấu gạch chéo '/' để tương thích cả Windows và Linux
BASE_STATIC_DIR = "static/uploads"
AVATAR_DIR = f"{BASE_STATIC_DIR}/avatars"
PRODUCT_DIR = f"{BASE_STATIC_DIR}/products"
MACHINE_LOG_DIR = f"{BASE_STATIC_DIR}/machine_logs"  # [SỬA] Đường dẫn riêng cho log máy

# --- HÀM TIỆN ÍCH ---
def save_file(file: UploadFile, directory: str) -> str:
    try:
        # 1. Tạo thư mục nếu chưa có
        if not os.path.exists(directory):
            os.makedirs(directory)

        # 2. Tạo tên file duy nhất (UUID) để tránh trùng lặp
        # Lấy đuôi file (ví dụ .jpg, .png)
        file_extension = os.path.splitext(file.filename)[1]
        # Tạo tên mới: machine_log_123e4567-e89b...jpg
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        
        file_location = f"{directory}/{unique_filename}"
        
        # 3. Ghi file vào ổ cứng
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # 4. Trả về đường dẫn URL (tương đối để lưu vào DB)
        # Ví dụ: /static/uploads/machine_logs/abc.jpg
        return f"/{file_location}" 
        
    except Exception as e:
        raise e

# --- ENDPOINTS ---

@router.post("/avatar")
async def upload_avatar(file: UploadFile = File(...)):
    try:
        file_path = save_file(file, AVATAR_DIR)
        # Trả về URL đầy đủ (hoặc tương đối tùy logic Frontend của bạn)
        return {"url": file_path} 
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi upload avatar: {str(e)}")

@router.post("/product")
async def upload_product_image(file: UploadFile = File(...)):
    try:
        file_path = save_file(file, PRODUCT_DIR)
        return {"url": file_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi upload ảnh sản phẩm: {str(e)}")

# [MỚI] API Upload ảnh sự cố máy
@router.post("/machine-logs")
async def upload_machine_log_image(file: UploadFile = File(...)):
    try:
        # Lưu vào thư mục machine_logs
        file_path = save_file(file, MACHINE_LOG_DIR)
        
        # Trả về đường dẫn để Frontend gửi kèm vào API update status
        return {"url": file_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi upload ảnh sự cố: {str(e)}")