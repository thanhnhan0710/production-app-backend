from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.schemas.user_schema import UserCreate, UserUpdate, UserResponse
from app.models.user import User
from app.services.user_service import user_service
from app.services.log_service import log_service

router = APIRouter()

@router.get("/", response_model=dict)
def read_users(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    keyword: Optional[str] = Query(None),
    role: Optional[str] = None,
    is_active: Optional[bool] = None,
    current_user: User = Depends(deps.get_current_active_user), # Yêu cầu phải login
) -> Any:
    """
    Lấy danh sách users (Có tìm kiếm & phân trang).
    """
    users, total = user_service.get_users(
        db, 
        skip=skip, 
        limit=limit, 
        keyword=keyword, 
        role=role, 
        is_active=is_active,
    )
    return {"data": users, "total": total, "skip": skip, "limit": limit}

@router.post("/", response_model=UserResponse)
def create_user(
    *,
    db: Session = Depends(deps.get_db),
    user_in: UserCreate,
    # Chỉ Admin mới được tạo user mới (hoặc bỏ dòng dưới nếu cho đăng ký tự do)
    current_user: User = Depends(deps.get_current_superuser), 
) -> Any:
    """
    Tạo user mới (Chỉ Admin).
    """
    user = user_service.get_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="User với email này đã tồn tại trong hệ thống.",
        )
    user = user_service.create_user(db, user=user_in)
    return user

@router.get("/me", response_model=UserResponse)
def read_user_me(
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Lấy thông tin của chính mình (Profile).
    """
    return current_user

@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    *,
    db: Session = Depends(deps.get_db),
    user_id: int,
    user_in: UserUpdate,
    current_user: User = Depends(deps.get_current_superuser),
):
    # 1. Lấy dữ liệu cũ trước khi update
    old_user = user_service.get_by_id(db, user_id=user_id)
    if not old_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Lưu lại trạng thái cũ để so sánh (Ví dụ đơn giản)
    old_data = {"email": old_user.email, "role": old_user.role}

    # 2. Thực hiện update
    updated_user = user_service.update_user(db, db_user=old_user, user_update=user_in)

    # 3. GHI LOG
    log_service.create_log(
        db=db,
        user_id=current_user.user_id, # Người thực hiện sửa
        action="UPDATE",
        target_type="User",
        target_id=updated_user.user_id,
        description=f"Admin {current_user.email} đã cập nhật user {updated_user.email}",
        changes={
            "before": old_data,
            "after": {"email": updated_user.email, "role": updated_user.role}
        }
    )
    
    return updated_user

@router.delete("/{user_id}", response_model=UserResponse)
def delete_user(
    *,
    db: Session = Depends(deps.get_db),
    user_id: int,
    current_user: User = Depends(deps.get_current_superuser), # Chỉ Admin
) -> Any:
    """
    Xóa User (Soft delete).
    """
    user = user_service.get_by_id(db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Không cho phép tự xóa chính mình
    if user.id == current_user.user_id:
         raise HTTPException(status_code=400, detail="Không thể xóa tài khoản đang đăng nhập")

    user = user_service.soft_delete_user(db, user_id=user_id)
    return user