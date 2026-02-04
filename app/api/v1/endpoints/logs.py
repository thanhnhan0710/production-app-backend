from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import inspect
from sqlalchemy.orm import Session, joinedload

from app.api import deps
from app.core.model_map import get_model_by_tablename
from app.schemas.log_schema import LogResponse
from app.models.log import Log
from app.models.user import User 

router = APIRouter()

# 1. READ LOGS (Chỉ Admin)
@router.get("/", response_model=List[LogResponse])
def read_logs(
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[int] = None,
    target_type: Optional[str] = None,
    db: Session = Depends(deps.get_db),
    # [BẢO MẬT] Chỉ Admin mới được xem log hệ thống
    current_user: User = Depends(deps.get_current_active_admin),
) -> Any:
    """
    Retrieve system logs. Restricted to Admins.
    """
    # Use joinedload to eagerly load the 'user' relationship
    query = db.query(Log).options(joinedload(Log.user))
    
    if user_id:
        query = query.filter(Log.user_id == user_id)
    if target_type:
        query = query.filter(Log.target_type == target_type)
        
    logs = query.order_by(Log.timestamp.desc()).offset(skip).limit(limit).all()
    
    # Map to response format
    results = []
    for log in logs:
        # Create a dict that matches LogResponse schema
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
            # Safely access user email
            "user_email": log.user.email if log.user else "Unknown"
        }
        results.append(log_dict)
    
    return results

# 2. REVERT LOG (Chỉ Admin)
@router.post("/{log_id}/revert")
def revert_log_change(
    log_id: int,
    db: Session = Depends(deps.get_db),
    # [BẢO MẬT] Chỉ Admin mới được hoàn tác dữ liệu
    current_user: User = Depends(deps.get_current_active_admin),
) -> Any:
    """
    Revert a specific change based on its log ID.
    Supports reverting UPDATE and DELETE actions. Restricted to Admins.
    """
    # 1. Find the Log entry
    log = db.query(Log).filter(Log.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Log entry not found")

    # 2. Identify the Model Class
    model_class = get_model_by_tablename(log.target_type)
    if not model_class:
        raise HTTPException(status_code=400, detail=f"Revert not supported for table '{log.target_type}'")

    # Identify the Primary Key column
    try:
        pk_column = inspect(model_class).primary_key[0]
    except Exception:
        raise HTTPException(status_code=500, detail="Could not determine primary key for model")

    # --- CASE 1: REVERT UPDATE ---
    if log.action == "UPDATE":
        if not log.changes or "old" not in log.changes:
            raise HTTPException(status_code=400, detail="No historical data available to revert")

        # Find the current object
        target_obj = db.query(model_class).filter(pk_column == log.target_id).first()
        if not target_obj:
            raise HTTPException(status_code=404, detail=f"Original data (ID {log.target_id}) has been deleted. Cannot revert update.")

        # Revert fields
        old_data = log.changes["old"]
        count = 0
        for key, value in old_data.items():
            if hasattr(target_obj, key):
                # Handle "None" string from JSON if necessary
                if value == "None": value = None
                setattr(target_obj, key, value)
                count += 1
        
        if count > 0:
            db.commit()
            db.refresh(target_obj)
        
        return {"message": "Update reverted successfully"}

    # --- CASE 2: REVERT DELETE ---
    elif log.action == "DELETE":
        if not log.changes or "old" not in log.changes:
            raise HTTPException(status_code=400, detail="No historical data available to restore")

        # Check if ID already exists to avoid conflicts
        existing_obj = db.query(model_class).filter(pk_column == log.target_id).first()
        if existing_obj:
            raise HTTPException(status_code=400, detail=f"Data with ID {log.target_id} already exists. Cannot restore.")

        # Prepare data for restoration
        restore_data = log.changes["old"]
        
        # Filter only valid columns for the model
        valid_columns = {c.key for c in inspect(model_class).mapper.column_attrs}
        clean_data = {k: v for k, v in restore_data.items() if k in valid_columns}

        # Handle "None" strings
        for k, v in clean_data.items():
            if v == "None": clean_data[k] = None

        try:
            # Create new instance with old data
            new_obj = model_class(**clean_data)
            db.add(new_obj)
            db.commit()
            db.refresh(new_obj)
            return {"message": f"Deleted data restored successfully (ID {log.target_id})"}
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Error restoring data: {str(e)}")

    # --- OTHER CASES ---
    else:
        raise HTTPException(status_code=400, detail=f"Revert not supported for action '{log.action}'")