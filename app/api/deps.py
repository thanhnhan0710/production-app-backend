from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.session import SessionLocal
from app.core.config import settings
# [CẬP NHẬT] Import thêm UserRole từ model
from app.models.user import User, UserRole 
from app.services.user_service import user_service

# Đường dẫn API dùng để login
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/login/access-token")

class TokenPayload(BaseModel):
    sub: Optional[str] = None

def get_db() -> Generator:
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

# 1. Xác thực Token & Lấy User
def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Không thể xác thực thông tin đăng nhập",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        token_data = TokenPayload(sub=user_id)
    except JWTError:
        raise credentials_exception
    
    # Lưu ý: user_service cần có hàm get_by_id
    user = user_service.get_by_id(db, user_id=int(token_data.sub))
    if not user:
        raise credentials_exception
    return user

# 2. Kiểm tra User có Active không
def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Tài khoản đã bị vô hiệu hóa")
    return current_user

# 3. [QUAN TRỌNG] Kiểm tra quyền Admin (Dựa trên Role Enum HOẶC Superuser)
def get_current_active_admin(
    current_user: User = Depends(get_current_active_user),
) -> User:
    # Logic: Cho phép nếu Role là ADMIN hoặc cờ is_superuser là True
    if current_user.role != UserRole.ADMIN and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền thực hiện thao tác này (Yêu cầu quyền Admin)"
        )
    return current_user

# (Tùy chọn) Kiểm tra quyền Manager nếu sau này cần
def get_current_active_manager(
    current_user: User = Depends(get_current_active_user),
) -> User:
    # Manager hoặc Admin đều được phép
    allowed_roles = [UserRole.ADMIN, UserRole.MANAGER]
    if current_user.role not in allowed_roles and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Yêu cầu quyền Quản lý trở lên"
        )
    return current_user