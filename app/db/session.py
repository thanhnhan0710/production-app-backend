from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Tạo engine kết nối
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)

# Tạo Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)