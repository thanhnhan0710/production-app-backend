import os
import uvicorn
# [THÊM] Import WebSocket và WebSocketDisconnect
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect 
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.router import api_router

# --- [THÊM] Import WebSockets Manager ---
from app.core.websockets import ws_manager
# ----------------------------------------

from app.core.context import set_current_user_id, user_id_context
from app.core.security import decode_token 
import app.db.audit 

app = FastAPI(
    title="Production Management API",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Tạo thư mục static nếu chưa có
if not os.path.exists("static"):
    os.makedirs("static")

# Mount thư mục static
app.mount("/static", StaticFiles(directory="static"), name="static")

# 1. MIDDLEWARE CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"], 
)

# 2. MIDDLEWARE AUDIT LOG
@app.middleware("http")
async def audit_log_middleware(request: Request, call_next):
    token_ctx = user_id_context.set(None)
    try:
        auth_header = request.headers.get("Authorization")
        if auth_header:
            parts = auth_header.split()
            if len(parts) == 2 and parts[0].lower() == "bearer":
                token = parts[1]
                payload = decode_token(token)
                user_id = payload.get("sub")
                if user_id:
                     set_current_user_id(int(user_id))
    except Exception as e:
        pass

    response = await call_next(request)
    user_id_context.reset(token_ctx)
    return response

# 3. [THÊM] ENDPOINT WEBSOCKET CHO FLUTTER KẾT NỐI
@app.websocket("/ws/updates")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            # Lệnh receive_text() giúp giữ kết nối luôn mở
            # Khi client (Flutter) ngắt kết nối, nó sẽ văng ra lỗi WebSocketDisconnect
            data = await websocket.receive_text()
            
            # (Tùy chọn) Có thể xử lý tin nhắn từ Flutter gửi lên tại đây nếu cần
            # print(f"Nhận từ Client: {data}")
            
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)

# Đăng ký router
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
def root():
    return {"message": "Welcome to Production Management API"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)


