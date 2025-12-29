from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.services.user_service import user_service
from app.core.config import settings

router = APIRouter()

@router.post("/access-token")
def login_access_token(
    db: Session = Depends(deps.get_db), form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    # 1. Tìm user theo email (username trong form OAuth2 mặc định là email)
    user = user_service.get_by_email(db, email=form_data.username)
    
    # 2. Kiểm tra password
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Sai email hoặc mật khẩu")
    
    # 3. Kiểm tra active
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Tài khoản chưa kích hoạt")

    # 4. Tạo token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": security.create_access_token(
            user.user_id, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }