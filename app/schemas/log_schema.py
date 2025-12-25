from typing import Optional, Any, Dict
from datetime import datetime
from pydantic import BaseModel

class LogBase(BaseModel):
    action: str
    target_type: Optional[str] = None
    target_id: Optional[int] = None
    description: Optional[str] = None
    changes: Optional[Dict[str, Any]] = None # JSON objects
    ip_address: Optional[str] = None

class LogCreate(LogBase):
    user_id: Optional[int] = None

class LogResponse(LogBase):
    id: int
    user_id: Optional[int] = None
    timestamp: datetime
    
    # Để hiện tên user thay vì chỉ hiện ID (nếu cần)
    user_email: Optional[str] = None 

    class Config:
        from_attributes = True