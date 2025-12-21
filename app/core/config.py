from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str
    DATABASE_URL: str

    class Config:
        env_file = ".env"

settings = Settings()