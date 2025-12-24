import sys
import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# 1. Thêm đường dẫn dự án vào sys.path để Alembic import được folder 'app'
sys.path.append(os.getcwd())

# 2. Import Settings và Base Model từ ứng dụng của bạn
from app.core.config import settings
from app.db.base import Base

# [QUAN TRỌNG] Import tất cả các Models để Alembic nhận diện được bảng
# Nếu không import ở đây, Alembic sẽ tưởng là chưa có bảng nào và xóa sạch DB cũ
from app.models.department import Department
from app.models.employee import Employee
from app.models.yarn import Yarn
from app.models.supplier import Supplier
from app.models.yarn_lot import YarnLot
from app.models.machine import Machine
from app.models.basket import Basket
from app.models.shift import Shift
from app.models.unit import Unit
from app.models.material import Material
from app.models.product import Product
from app.models.yarn_issue_slip import YarnIssueSlip
from app.models.yarn_issue_slip_detail import YarnIssueSlipDetail
from app.models.material_issue_slip import MaterialIssueSlip
from app.models.material_issue_slip_detail import MaterialIssueSlipDetail
from app.models.work_schedule import WorkSchedule
from app.models.weaving_basket_ticket import WeavingBasketTicket
from app.models.weaving_inspection import WeavingInspection
from app.models.standard import Standard
from app.models.dye_color import DyeColor
from app.models.inventory_semi import SemiFinishedImportTicket, SemiFinishedImportDetail, SemiFinishedExportTicket, SemiFinishedExportDetail



# 3. Lấy config từ alembic.ini
config = context.config

# 4. Setup loggers
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 5. Gán Metadata của SQLAlchemy model cho Alembic
target_metadata = Base.metadata

# 6. Ghi đè URL kết nối DB bằng biến môi trường (Thay vì hardcode trong alembic.ini)
# Điều này giúp bảo mật và linh hoạt khi deploy
# Dòng đã sửa (Thêm .replace("%", "%%"))
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL.replace("%", "%%"))

def run_migrations_offline() -> None:
    """Chạy migration ở chế độ 'offline'.
    Dùng để generate file SQL mà không cần kết nối DB thực tế (ít dùng).
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Chạy migration ở chế độ 'online'.
    Kết nối trực tiếp vào DB để so sánh và cập nhật.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()