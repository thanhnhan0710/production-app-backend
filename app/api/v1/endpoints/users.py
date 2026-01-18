from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.schemas.user_schema import UserCreate, UserUpdate, UserResponse, UserListResponse
from app.models.user import User
from app.services.user_service import user_service

router = APIRouter()

<<<<<<< HEAD
=======
# 1. GET LIST (Sửa response_model thành UserListResponse)
>>>>>>> c468be65d7388abd40a800c84aa27cfe56d2c0d3
@router.get("/", response_model=UserListResponse)
def read_users(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    keyword: Optional[str] = Query(None),
    role: Optional[str] = None,
<<<<<<< HEAD
    # [LƯU Ý]: Frontend không gửi is_active, nghĩa là is_active=None. 
    # Backend sẽ trả về cả user Active và Inactive (đã xóa mềm).
    # Nếu bạn chỉ muốn hiện user chưa xóa, hãy đổi default thành True.
    is_active: Optional[bool] = None, 
=======
    is_active: Optional[bool] = None,
>>>>>>> c468be65d7388abd40a800c84aa27cfe56d2c0d3
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    # ... (Giữ nguyên logic gọi user_service) ...
    users, total = user_service.get_users(
        db, 
        skip=skip, 
        limit=limit, 
        keyword=keyword, 
        role=role, 
        is_active=is_active,
    )
    # FastAPI sẽ tự động map list User objects vào list UserResponse nhờ from_attributes=True
    return {"data": users, "total": total, "skip": skip, "limit": limit}

# 2. CREATE USER
@router.post("/", response_model=UserResponse)
def create_user(
    *,
    db: Session = Depends(deps.get_db),
    user_in: UserCreate,
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

# 3. GET ME (Đây là API gây lỗi Auth Error nếu schema sai)
@router.get("/me", response_model=UserResponse)
def read_user_me(
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Lấy thông tin của chính mình (Profile).
    UserResponse sẽ tự động map object `current_user` từ DB thành JSON.
    """
    return current_user

# 4. UPDATE USER
@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    *,
    db: Session = Depends(deps.get_db),
    user_id: int,
    user_in: UserUpdate,
    current_user: User = Depends(deps.get_current_superuser),
):
    old_user = user_service.get_by_id(db, user_id=user_id)
    if not old_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    updated_user = user_service.update_user(db, db_user=old_user, user_update=user_in)
    return updated_user

# 5. DELETE USER
@router.delete("/{user_id}", response_model=UserResponse)
def delete_user(
    *,
    db: Session = Depends(deps.get_db),
    user_id: int,
    current_user: User = Depends(deps.get_current_superuser),
) -> Any:
    user = user_service.get_by_id(db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.user_id == current_user.user_id:
         raise HTTPException(status_code=400, detail="Không thể xóa tài khoản đang đăng nhập")

    user = user_service.soft_delete_user(db, user_id=user_id)
    return user