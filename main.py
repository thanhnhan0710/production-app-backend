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
    token_ctx = user_id_context.set(None)
    try:
        auth_header = request.headers.get("Authorization")
        if auth_header:
            # Dùng split thay vì partition để an toàn hơn với khoảng trắng
            parts = auth_header.split()
            if len(parts) == 2 and parts[0].lower() == "bearer":
                token = parts[1]
                payload = decode_token(token)
                # Lấy user_id, ép kiểu int nếu DB dùng int
                user_id = payload.get("sub")
                if user_id:
                     set_current_user_id(int(user_id))
    except Exception as e:
        # Log lỗi token nếu cần thiết, nhưng không chặn request
        # print(f"Auth Middleware Error: {e}")
        pass

    response = await call_next(request)
    user_id_context.reset(token_ctx)
    return response
# -------------------------------------------------------

# Đăng ký router
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
def root():
    return {"message": "Welcome to Production Management API"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)