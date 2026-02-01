import datetime
import uuid
from sqlalchemy import event, inspect
from sqlalchemy.orm import Session
from app.models.log import Log
from app.core.context import get_current_user_id

# 1. Helper chuyển đổi dữ liệu
def serialize_value(val):
    if isinstance(val, (datetime.date, datetime.datetime)):
        return val.isoformat()
    if isinstance(val, uuid.UUID):
        return str(val)
    return val

# 2. Helper lấy giá trị Khóa chính (Primary Key) ĐỘNG
def get_pk_value(obj):
    """
    Tự động tìm khóa chính của bảng (id, machine_id, user_id...) và lấy giá trị.
    """
    try:
        state = inspect(obj)
        # Cách 1: Lấy từ identity (Thường có ngay sau khi flush)
        if state.identity:
            return state.identity[0]
        
        # Cách 2: Nếu chưa có identity, soi vào Mapper để lấy tên cột PK
        pk_column = state.mapper.primary_key[0]
        return getattr(obj, pk_column.key, None)
    except Exception:
        return None

# 3. Helper lấy toàn bộ dữ liệu (Create/Delete)
def get_full_data(obj):
    data = {}
    state = inspect(obj)
    for attr in state.mapper.column_attrs:
        key = attr.key
        val = getattr(obj, key, None)
        data[key] = serialize_value(val)
    return data

# 4. Helper lấy dữ liệu thay đổi (Update)
def get_changes_diff(obj):
    state = inspect(obj)
    changes = {"old": {}, "new": {}}
    has_change = False

    for attr in state.attrs:
        # Bỏ qua các field không quan trọng
        if attr.key in ["created_at", "updated_at", "updated_by_id"] or attr.history.has_changes() is False:
            continue
            
        hist = attr.history
        if hist.has_changes():
            old_val = hist.deleted[0] if hist.deleted else None
            new_val = hist.added[0] if hist.added else None
            
            changes["old"][attr.key] = serialize_value(old_val)
            changes["new"][attr.key] = serialize_value(new_val)
            has_change = True
            
    return changes if has_change else None

# 5. Listener chính
@event.listens_for(Session, 'after_flush')
def receive_after_flush(session, flush_context):
    user_id = get_current_user_id()
    logs_to_create = []

    # --- XỬ LÝ TẠO MỚI (INSERT) ---
    for obj in session.new:
        if isinstance(obj, Log): continue 
        
        # [SỬA LỖI] Dùng hàm helper để lấy ID chính xác
        obj_id = get_pk_value(obj)
        new_data = get_full_data(obj)
        
        logs_to_create.append(Log(
            user_id=user_id,
            action="CREATE",
            target_type=obj.__tablename__,
            target_id=obj_id, # Không còn bị null nữa
            description=f"Tạo mới {obj.__tablename__}",
            changes={"old": {}, "new": new_data},
            ip_address="System"
        ))

    # --- XỬ LÝ CẬP NHẬT (UPDATE) ---
    for obj in session.dirty:
        if isinstance(obj, Log): continue
        if not session.is_modified(obj): continue

        changes = get_changes_diff(obj)
        # [SỬA LỖI] Dùng hàm helper ở đây luôn
        obj_id = get_pk_value(obj)

        if changes:
            logs_to_create.append(Log(
                user_id=user_id,
                action="UPDATE",
                target_type=obj.__tablename__,
                target_id=obj_id, # Không còn bị null nữa
                description=f"Cập nhật {obj.__tablename__}",
                changes=changes
            ))

    # --- XỬ LÝ XÓA (DELETE) ---
    for obj in session.deleted:
        if isinstance(obj, Log): continue
        
        obj_id = get_pk_value(obj)
        old_data = get_full_data(obj)
        
        logs_to_create.append(Log(
            user_id=user_id,
            action="DELETE",
            target_type=obj.__tablename__,
            target_id=obj_id, # Không còn bị null nữa
            description=f"Xóa {obj.__tablename__}",
            changes={"old": old_data, "new": {}}
        ))

    for log in logs_to_create:
        session.add(log)