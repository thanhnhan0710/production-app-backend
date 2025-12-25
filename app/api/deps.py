from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.session import SessionLocal
from app.core.config import settings
from app.models.user import User
from app.services.user_service import user_service

# Đường dẫn API dùng để login (để Swagger UI biết nút Authorize trỏ về đâu)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"/api/v1/login/access-token")

class TokenPayload(BaseModel):
    sub: Optional[str] = None

def get_db() -> Generator:
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

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
    
    user = user_service.get_by_id(db, user_id=int(token_data.sub))
    if not user:
        raise credentials_exception
    return user

def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Tài khoản đã bị vô hiệu hóa")
    return current_user

def get_current_superuser(
    current_user: User = Depends(get_current_active_user),
) -> User:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=400, detail="Người dùng không có đủ quyền hạn (cần Admin)"
        )
    return current_user