import sys
import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context

# ------------------------------------------------------------------------
# 1. Cấu hình đường dẫn (Path Setup)
# ------------------------------------------------------------------------
# Thêm thư mục gốc của dự án vào sys.path để Python tìm thấy module 'app'
# Sử dụng abspath để đảm bảo đường dẫn chính xác dù chạy lệnh ở đâu
current_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(current_path)

# ------------------------------------------------------------------------
# 2. Import Settings và Base Model
# ------------------------------------------------------------------------
from app.core.config import settings

# [QUAN TRỌNG] Import Base từ 'app.db.base' thay vì 'app.db.base_class'
# Vì file 'app/db/base.py' của bạn đã import tất cả các Models (User, Product, Material...)
# nên Base.metadata lúc này đã chứa đầy đủ thông tin các bảng.
from app.db.base import Base 

# ------------------------------------------------------------------------
# 3. Config Alembic
# ------------------------------------------------------------------------
config = context.config

# Setup loggers
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Gán Metadata của SQLAlchemy model cho Alembic
target_metadata = Base.metadata

# ------------------------------------------------------------------------
# 4. Ghi đè URL Database từ biến môi trường
# ------------------------------------------------------------------------
# Lấy URL từ settings (file .env)
db_url = str(settings.DATABASE_URL)

# Fix lỗi ký tự '%' trong mật khẩu (ConfigParser của Python hiểu nhầm % là biến)
if "%" in db_url:
    db_url = db_url.replace("%", "%%")

config.set_main_option("sqlalchemy.url", db_url)


def run_migrations_offline() -> None:
    """Chạy migration ở chế độ 'offline'.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True, # [Option] So sánh cả kiểu dữ liệu column (VARCHAR thay đổi độ dài...)
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Chạy migration ở chế độ 'online'.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata,
            compare_type=True, # [Option] So sánh cả thay đổi về kiểu dữ liệu
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()