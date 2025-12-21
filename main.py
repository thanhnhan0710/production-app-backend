import uvicorn
from fastapi import FastAPI
from app.core.config import settings
from app.api.v1.router import api_router



app = FastAPI(
    title="Production Management API",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Đăng ký router
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
def root():
    return {"message": "Welcome to Production Management API"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)