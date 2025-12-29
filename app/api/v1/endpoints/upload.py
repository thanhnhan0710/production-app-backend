import os
import shutil
from fastapi import APIRouter, UploadFile, File, HTTPException

router = APIRouter()

# Đường dẫn thư mục muốn lưu (Tính từ root của project)
UPLOAD_DIR = "static/uploads/avatars"

@router.post("/avatar")
async def upload_avatar(file: UploadFile = File(...)):
    try:
        # 1. Kiểm tra và TỰ ĐỘNG TẠO thư mục nếu chưa có
        if not os.path.exists(UPLOAD_DIR):
            os.makedirs(UPLOAD_DIR)

        # 2. Tạo đường dẫn file
        # Lưu ý: Nên đổi tên file để tránh trùng (ví dụ dùng uuid), ở đây giữ nguyên theo demo
        file_location = f"{UPLOAD_DIR}/{file.filename}"
        
        # 3. Ghi file vào ổ cứng
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # 4. Trả về URL để Frontend hiển thị
        # Lưu ý: Khi deploy cần thay localhost bằng biến môi trường DOMAIN
        return {"url": f"http://localhost:8000/{file_location}"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))