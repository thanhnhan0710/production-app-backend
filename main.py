import os
import uvicorn
from fastapi import FastAPI, Request  # [THÊM] Import Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.router import api_router

# --- [THÊM] Import cho Audit Log ---
from app.core.context import set_current_user_id, user_id_context
# Import hàm decode token (giả định bạn để trong security.py)
# Nếu file của bạn khác, hãy sửa đường dẫn import này
from app.core.security import decode_token 
# Import module audit để đăng ký các Event Listener với SQLAlchemy
import app.db.audit 
# -----------------------------------

app = FastAPI(
    title="Production Management API",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Tạo thư mục static nếu chưa có
if not os.path.exists("static"):
    os.makedirs("static")

# Mount thư mục static
app.mount("/static", StaticFiles(directory="static"), name="static")

# 1. MIDDLEWARE CORS (Giữ nguyên)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"], 
)

# 2. [THÊM] MIDDLEWARE AUDIT LOG (Bắt User ID từ Token)
# Middleware này sẽ chạy trước mỗi request để lấy User ID
@app.middleware("http")
async def audit_log_middleware(request: Request, call_next):
    # a. Reset context (đặt về None) để tránh dùng nhầm ID của request trước đó
    token = user_id_context.set(None)
    
    try:
        # b. Lấy header Authorization
        auth_header = request.headers.get("Authorization")
        if auth_header:
            # Định dạng chuẩn: "Bearer <token>"
            scheme, _, param = auth_header.partition(" ")
            if scheme.lower() == 'bearer':
                # Giải mã token để lấy user_id (sub)
                payload = decode_token(param)
                user_id = payload.get("sub") # Hoặc payload.get("id") tùy cách bạn tạo token
                
                if user_id:
                    # Lưu user_id vào biến toàn cục (ContextVar)
                    # SQLAlchemy Listener sẽ đọc biến này
                    set_current_user_id(int(user_id))
    except Exception as e:
        # Nếu token lỗi hoặc hết hạn, ta cứ để user_id là None (Khách/Lỗi)
        # Không được raise lỗi ở đây để tránh làm chết request
        pass 

    # c. Tiếp tục xử lý request (vào router, controller...)
    response = await call_next(request)
    
    # d. Dọn dẹp context sau khi request xong
    user_id_context.reset(token)
    
    return response
# -------------------------------------------------------

# Đăng ký router
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
def root():
    return {"message": "Welcome to Production Management API"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)