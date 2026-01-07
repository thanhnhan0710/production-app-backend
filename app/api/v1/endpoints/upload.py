import os
import shutil
from fastapi import APIRouter, UploadFile, File, HTTPException

router = APIRouter()

# --- CẤU HÌNH ĐƯỜNG DẪN ---
BASE_STATIC_DIR = "static/uploads"
AVATAR_DIR = f"{BASE_STATIC_DIR}/avatars"
PRODUCT_DIR = f"{BASE_STATIC_DIR}/products"

# Hàm tiện ích để lưu file (tránh lặp code)
def save_file(file: UploadFile, directory: str) -> str:
    try:
        # 1. Tạo thư mục nếu chưa có
        if not os.path.exists(directory):
            os.makedirs(directory)

        # 2. Đường dẫn file (Lưu ý: Thực tế nên đổi tên file bằng uuid để tránh trùng)
        file_location = f"{directory}/{file.filename}"
        
        # 3. Ghi file
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # 4. Trả về đường dẫn tương đối để tạo URL
        return file_location
    except Exception as e:
        raise e

# --- ENDPOINTS ---

@router.post("/avatar")
async def upload_avatar(file: UploadFile = File(...)):
    try:
        file_path = save_file(file, AVATAR_DIR)
        # Thay localhost bằng domain thực tế khi deploy
        return {"url": f"http://localhost:8000/{file_path}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi upload avatar: {str(e)}")

@router.post("/product")
async def upload_product_image(file: UploadFile = File(...)):
    try:
        file_path = save_file(file, PRODUCT_DIR)
        return {"url": f"http://localhost:8000/{file_path}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi upload ảnh sản phẩm: {str(e)}")