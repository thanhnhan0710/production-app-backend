from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks # [MỚI] Thêm BackgroundTasks
from sqlalchemy.orm import Session

from app.api import deps
from app.schemas.user_schema import UserCreate, UserUpdate, UserResponse, UserListResponse
from app.models.user import User
from app.services.user_service import user_service
from app.core.websockets import ws_manager # [MỚI] Import WebSocket Manager

router = APIRouter()

# 1. GET LIST - Xem danh sách User
@router.get("/", response_model=UserListResponse)
def read_users(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    keyword: Optional[str] = Query(None),
    role: Optional[str] = None,
    is_active: Optional[bool] = None, 
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

# 2. CREATE USER - Tạo user mới (Có WebSocket)
@router.post("/", response_model=UserResponse)
def create_user(
    *,
    db: Session = Depends(deps.get_db),
    user_in: UserCreate,
    background_tasks: BackgroundTasks, # [MỚI]
    current_user: User = Depends(deps.get_current_active_admin), 
) -> Any:
    user = user_service.get_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="Email này đã được sử dụng.",
        )
    user = user_service.create_user(db, user=user_in)
    
    # [MỚI] Bắn tín hiệu WebSocket
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_USERS")
    return user

# 3. GET ME - Xem thông tin chính mình
@router.get("/me", response_model=UserResponse)
def read_user_me(
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    return current_user

# 4. UPDATE USER - Sửa thông tin User khác (Có WebSocket)
@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    *,
    db: Session = Depends(deps.get_db),
    user_id: int,
    user_in: UserUpdate,
    background_tasks: BackgroundTasks, # [MỚI]
    current_user: User = Depends(deps.get_current_active_admin),
):
    old_user = user_service.get_by_id(db, user_id=user_id)
    if not old_user:
        raise HTTPException(status_code=404, detail="User not found")

    updated_user = user_service.update_user(db, db_user=old_user, user_update=user_in)
    
    # [MỚI] Bắn tín hiệu WebSocket
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_USERS")
    return updated_user

# 5. DELETE USER - Xóa User (Có WebSocket)
@router.delete("/{user_id}", response_model=UserResponse)
def delete_user(
    *,
    db: Session = Depends(deps.get_db),
    user_id: int,
    background_tasks: BackgroundTasks, # [MỚI]
    current_user: User = Depends(deps.get_current_active_admin),
) -> Any:
    user = user_service.get_by_id(db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Bảo vệ an toàn: Không cho phép tự xóa chính mình
    if user.user_id == current_user.user_id:
         raise HTTPException(status_code=400, detail="Không thể xóa tài khoản đang đăng nhập")

    user = user_service.soft_delete_user(db, user_id=user_id)
    
    # [MỚI] Bắn tín hiệu WebSocket
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_USERS")
    return user