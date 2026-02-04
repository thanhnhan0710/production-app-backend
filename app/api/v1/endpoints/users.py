from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.schemas.user_schema import UserCreate, UserUpdate, UserResponse, UserListResponse
from app.models.user import User
from app.services.user_service import user_service

router = APIRouter()

# 1. GET LIST - Xem danh sách User
# [PHÂN QUYỀN]: Chỉ Admin mới được xem danh sách
@router.get("/", response_model=UserListResponse)
def read_users(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    keyword: Optional[str] = Query(None),
    role: Optional[str] = None,
    is_active: Optional[bool] = None, 
    # [CẬP NHẬT] Thay get_current_active_user -> get_current_active_admin
    current_user: User = Depends(deps.get_current_active_admin),
) -> Any:
    users, total = user_service.get_users(
        db, 
        skip=skip, 
        limit=limit, 
        keyword=keyword, 
        role=role, 
        is_active=is_active,
    )
    return {"data": users, "total": total, "skip": skip, "limit": limit}

# 2. CREATE USER - Tạo user mới
# [PHÂN QUYỀN]: Chỉ Admin mới được tạo nhân viên mới
@router.post("/", response_model=UserResponse)
def create_user(
    *,
    db: Session = Depends(deps.get_db),
    user_in: UserCreate,
    # [CẬP NHẬT] Thay get_current_superuser -> get_current_active_admin
    current_user: User = Depends(deps.get_current_active_admin), 
) -> Any:
    user = user_service.get_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="Email này đã được sử dụng.",
        )
    user = user_service.create_user(db, user=user_in)
    return user

# 3. GET ME - Xem thông tin chính mình
# [PHÂN QUYỀN]: Ai đăng nhập cũng xem được (Staff, Manager, Admin...)
# Giữ nguyên get_current_active_user
@router.get("/me", response_model=UserResponse)
def read_user_me(
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    return current_user

# 4. UPDATE USER - Sửa thông tin User khác
# [PHÂN QUYỀN]: Chỉ Admin mới được sửa thông tin người khác
@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    *,
    db: Session = Depends(deps.get_db),
    user_id: int,
    user_in: UserUpdate,
    # [CẬP NHẬT] Thay get_current_superuser -> get_current_active_admin
    current_user: User = Depends(deps.get_current_active_admin),
):
    old_user = user_service.get_by_id(db, user_id=user_id)
    if not old_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Logic nghiệp vụ bổ sung (nếu cần): Không cho phép hạ cấp chính mình
    # if old_user.user_id == current_user.user_id and user_in.role != UserRole.ADMIN: ...

    updated_user = user_service.update_user(db, db_user=old_user, user_update=user_in)
    return updated_user

# 5. DELETE USER - Xóa User
# [PHÂN QUYỀN]: Chỉ Admin mới được xóa
@router.delete("/{user_id}", response_model=UserResponse)
def delete_user(
    *,
    db: Session = Depends(deps.get_db),
    user_id: int,
    # [CẬP NHẬT] Thay get_current_superuser -> get_current_active_admin
    current_user: User = Depends(deps.get_current_active_admin),
) -> Any:
    user = user_service.get_by_id(db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Bảo vệ an toàn: Không cho phép tự xóa chính mình
    if user.user_id == current_user.user_id:
         raise HTTPException(status_code=400, detail="Không thể xóa tài khoản đang đăng nhập")

    user = user_service.soft_delete_user(db, user_id=user_id)
    return user