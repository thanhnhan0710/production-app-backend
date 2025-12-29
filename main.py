import os
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles # Import này
# 1. Import CORSMiddleware
from fastapi.middleware.cors import CORSMiddleware 
from app.core.config import settings
from app.api.v1.router import api_router

app = FastAPI(
    title="Production Management API",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Tạo thư mục static nếu chưa có để tránh lỗi khi khởi động
if not os.path.exists("static"):
    os.makedirs("static")

# Mount thư mục static
app.mount("/static", StaticFiles(directory="static"), name="static")

# 2. THÊM MIDDLEWARE ĐỂ GIẢI QUYẾT LỖI KẾT NỐI (CORS)
# Cần thiết cho Flutter Web chạy trên cổng khác (ví dụ: 57797) khi gọi API trên cổng 8000
app.add_middleware(
    CORSMiddleware,
    # Cho phép tất cả các nguồn (Flutter Web, Postman, etc.) truy cập.
    # Khi deploy Production, bạn nên thay "*" bằng tên miền thật của Flutter App.
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"], # Cho phép các phương thức POST, GET, PUT, DELETE...
    allow_headers=["*"], # Cho phép các header như Authorization (chứa Token)
)
# END MIDDLEWARE

# Đăng ký router
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
def root():
    return {"message": "Welcome to Production Management API"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)