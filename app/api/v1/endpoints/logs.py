from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import inspect
from sqlalchemy.orm import Session, joinedload # [QUAN TRỌNG] Thêm joinedload

from app.api import deps
from app.core.model_map import get_model_by_tablename
from app.schemas.log_schema import LogResponse
from app.models.log import Log
from app.models.user import User # Import model User

router = APIRouter()

@router.get("/", response_model=List[LogResponse])
def read_logs(
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[int] = None,
    target_type: Optional[str] = None,
    db: Session = Depends(deps.get_db),
) -> Any:
    # [SỬA LỖI] Thêm options joinedload để lấy thông tin User
    query = db.query(Log).options(joinedload(Log.user))
    
    if user_id:
        query = query.filter(Log.user_id == user_id)
    if target_type:
        query = query.filter(Log.target_type == target_type)
        
    logs = query.order_by(Log.timestamp.desc()).offset(skip).limit(limit).all()
    
    # Map dữ liệu User vào response (nếu Schema chưa tự map)
    # Tuy nhiên, nếu LogResponse config from_attributes=True và có field user_email
    # Bạn cần đảm bảo schema LogResponse lấy được email.
    
    results = []
    for log in logs:
        # Chuyển object SQLAlchemy sang dict cơ bản
        log_dict = {
            "id": log.id,
            "user_id": log.user_id,
            "action": log.action,
            "target_type": log.target_type,
            "target_id": log.target_id,
            "description": log.description,
            "changes": log.changes,
            "ip_address": log.ip_address,
            "timestamp": log.timestamp,
            # Tự lấy email từ relation
            "user_email": log.user.email if log.user else "Unknown"
        }
        results.append(log_dict)
    
    return results

@router.post("/{log_id}/revert")
def revert_log_change(
    log_id: int,
    db: Session = Depends(deps.get_db),
) -> Any:
    # 1. Tìm Log
    log = db.query(Log).filter(Log.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Không tìm thấy nhật ký")

    # 2. Xác định Model Class
    model_class = get_model_by_tablename(log.target_type)
    if not model_class:
        raise HTTPException(status_code=400, detail=f"Không hỗ trợ khôi phục cho bảng '{log.target_type}'")

    # Xác định cột khóa chính (PK)
    try:
        pk_column = inspect(model_class).primary_key[0]
    except Exception:
        raise HTTPException(status_code=500, detail="Lỗi xác định khóa chính")

    # --- TRƯỜNG HỢP 1: HOÀN TÁC CẬP NHẬT (UPDATE) ---
    if log.action == "UPDATE":
        if not log.changes or "old" not in log.changes:
            raise HTTPException(status_code=400, detail="Không có dữ liệu cũ để khôi phục")

        # Tìm đối tượng hiện tại
        target_obj = db.query(model_class).filter(pk_column == log.target_id).first()
        if not target_obj:
            raise HTTPException(status_code=404, detail=f"Dữ liệu gốc (ID {log.target_id}) đã bị xóa, không thể hoàn tác update.")

        # Revert
        old_data = log.changes["old"]
        count = 0
        for key, value in old_data.items():
            if hasattr(target_obj, key):
                if value == "None": value = None
                setattr(target_obj, key, value)
                count += 1
        
        if count > 0:
            db.commit()
            db.refresh(target_obj)
        
        return {"message": "Đã hoàn tác cập nhật thành công"}

    # --- TRƯỜNG HỢP 2: HOÀN TÁC XÓA (DELETE) ---
    elif log.action == "DELETE":
        if not log.changes or "old" not in log.changes:
            raise HTTPException(status_code=400, detail="Không có dữ liệu cũ để khôi phục")

        # Kiểm tra xem ID đó đã tồn tại lại chưa (tránh lỗi Duplicate Key)
        existing_obj = db.query(model_class).filter(pk_column == log.target_id).first()
        if existing_obj:
            raise HTTPException(status_code=400, detail=f"Dữ liệu với ID {log.target_id} đang tồn tại, không thể khôi phục chồng lên.")

        # Lấy dữ liệu cũ để tạo mới (Restore)
        restore_data = log.changes["old"]
        
        # Tạo object mới từ dữ liệu cũ (bao gồm cả ID nếu có trong restore_data)
        # Lưu ý: Cần filter các key hợp lệ trong model để tránh lỗi nếu JSON lưu thừa
        valid_columns = {c.key for c in inspect(model_class).mapper.column_attrs}
        clean_data = {k: v for k, v in restore_data.items() if k in valid_columns}

        # Xử lý các giá trị "None" chuỗi thành None thật
        for k, v in clean_data.items():
            if v == "None": clean_data[k] = None

        try:
            # Tạo instance mới
            new_obj = model_class(**clean_data)
            db.add(new_obj)
            db.commit()
            db.refresh(new_obj)
            return {"message": f"Đã khôi phục dữ liệu đã xóa (ID {log.target_id})"}
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Lỗi khi khôi phục: {str(e)}")

    # --- TRƯỜNG HỢP KHÁC ---
    else:
        raise HTTPException(status_code=400, detail=f"Chưa hỗ trợ hoàn tác cho hành động {log.action}")