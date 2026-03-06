from pydantic import BaseModel, ConfigDict
from typing import Optional

class POStatusBase(BaseModel):
    status_code: str
    description: Optional[str] = None

class POStatusCreate(POStatusBase):
    pass

class POStatusUpdate(BaseModel):
    status_code: Optional[str] = None
    description: Optional[str] = None

class POStatusResponse(POStatusBase):
    status_id: int
    
    model_config = ConfigDict(from_attributes=True)