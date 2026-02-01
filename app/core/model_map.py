# app/core/model_map.py
from app.models.machine import Machine
from app.models.product import Product
from app.models.user import User
# Import thêm các model khác của bạn ở đây...

# Dictionary ánh xạ: "tên_bảng" -> ModelClass
MODEL_MAPPING = {
    "machines": Machine,
    "products": Product,
    "users": User,
    # Thêm các bảng khác vào đây...
}

def get_model_by_tablename(tablename: str):
    return MODEL_MAPPING.get(tablename)