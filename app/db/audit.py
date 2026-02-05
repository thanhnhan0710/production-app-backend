import datetime
import uuid
import enum  # [THÊM] Import Enum
from decimal import Decimal # [THÊM] Import Decimal để sửa lỗi chính
from sqlalchemy import event, inspect
from sqlalchemy.orm import Session
from app.models.log import Log
from app.core.context import get_current_user_id

# 1. Helper chuyển đổi dữ liệu (Đã sửa lỗi)
def serialize_value(val):
    if val is None:
        return None
    # Xử lý ngày tháng
    if isinstance(val, (datetime.date, datetime.datetime)):
        return val.isoformat()
    # Xử lý UUID
    if isinstance(val, uuid.UUID):
        return str(val)
    # [FIX QUAN TRỌNG] Xử lý Decimal -> float để lưu JSON
    if isinstance(val, Decimal):
        return float(val)
    # [BỔ SUNG] Xử lý Enum (nếu có dùng trong model)
    if isinstance(val, enum.Enum):
        return val.value
    if hasattr(val, '_sa_instance_state'):
        return f"<{val.__class__.__name__} ID={get_pk_value(val)}>"
    return val

# 2. Helper lấy giá trị Khóa chính (Giữ nguyên)
def get_pk_value(obj):
    try:
        state = inspect(obj)
        if state.identity:
            return state.identity[0]
        pk_column = state.mapper.primary_key[0]
        return getattr(obj, pk_column.key, None)
    except Exception:
        return None

# 3. Helper lấy toàn bộ dữ liệu (Giữ nguyên)
def get_full_data(obj):
    data = {}
    state = inspect(obj)
    # Chỉ lấy các cột (column_attrs), tránh lấy relationship
    for attr in state.mapper.column_attrs:
        key = attr.key
        val = getattr(obj, key, None)
        data[key] = serialize_value(val)
    return data

def get_changes_diff(obj):
    state = inspect(obj)
    changes = {"old": {}, "new": {}}
    has_change = False

    for attr in state.attrs:
        # [QUAN TRỌNG] Bỏ qua nếu attribute này là một Relationship (Mối quan hệ bảng)
        # Chúng ta chỉ log sự thay đổi của các cột (Columns)
        if attr.key in state.mapper.relationships:
            continue

        # Bỏ qua các field không quan trọng
        if attr.key in ["created_at", "updated_at", "updated_by_id", "modified_at"]:
            continue
            
        # Kiểm tra history
        if not hasattr(attr, 'history'):
            continue

        hist = attr.history
        if not hist.has_changes():
            continue

        # Lấy giá trị cũ và mới
        old_val = hist.deleted[0] if hist.deleted else None
        new_val = hist.added[0] if hist.added else None

        # Serialize
        changes["old"][attr.key] = serialize_value(old_val)
        changes["new"][attr.key] = serialize_value(new_val)
        has_change = True
            
    return changes if has_change else None

# 5. Listener chính (Logic tốt, giữ nguyên)
@event.listens_for(Session, 'after_flush')
def receive_after_flush(session, flush_context):
    try:
        user_id = get_current_user_id()
    except:
        user_id = None # Fallback nếu không lấy được context
        
    logs_to_create = []

    # --- INSERT ---
    for obj in session.new:
        if isinstance(obj, Log): continue
        
        obj_id = get_pk_value(obj)
        new_data = get_full_data(obj)
        
        logs_to_create.append(Log(
            user_id=user_id,
            action="CREATE",
            target_type=obj.__tablename__,
            target_id=obj_id,
            description=f"Tạo mới {obj.__tablename__}",
            changes={"old": {}, "new": new_data},
            ip_address="System" # Có thể cải tiến lấy IP từ context nếu cần
        ))

    # --- UPDATE ---
    for obj in session.dirty:
        if isinstance(obj, Log): continue
        if not session.is_modified(obj): continue

        changes = get_changes_diff(obj)
        obj_id = get_pk_value(obj)

        if changes:
            logs_to_create.append(Log(
                user_id=user_id,
                action="UPDATE",
                target_type=obj.__tablename__,
                target_id=obj_id,
                description=f"Cập nhật {obj.__tablename__}",
                changes=changes
            ))

    # --- DELETE ---
    for obj in session.deleted:
        if isinstance(obj, Log): continue
        
        obj_id = get_pk_value(obj)
        old_data = get_full_data(obj)
        
        logs_to_create.append(Log(
            user_id=user_id,
            action="DELETE",
            target_type=obj.__tablename__,
            target_id=obj_id,
            description=f"Xóa {obj.__tablename__}",
            changes={"old": old_data, "new": {}}
        ))

    # Lưu log
    for log in logs_to_create:
        session.add(log)