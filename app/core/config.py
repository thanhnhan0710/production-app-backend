from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # 1. Các biến cơ bản
    API_V1_STR: str = "/api/v1"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 ngày
    
    # 2. Các biến nhạy cảm (Nên để Optional hoặc không gán mặc định để bắt buộc phải có trong .env)
    SECRET_KEY: str
    DATABASE_URL: str

    # 3. Cấu hình mới của Pydantic v2
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"  # Bỏ qua các biến thừa trong .env
    )

settings = Settings()