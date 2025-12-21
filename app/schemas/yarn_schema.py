from pydantic import BaseModel, EmailStr
from typing import Optional

class YarnBase(BaseModel):
    yarn_name: str
    item_code: str
    type: Optional[str] = None
    color:str
    origin: str
    supplier_id: int
    note:Optional[str] = None

class YarnCreate(YarnBase):
    pass

class YarnUpdate(BaseModel):
    yarn_name: Optional[str] = None
    item_code: Optional[str] = None
    type: Optional[str] = None
    color:Optional[str] = None
    origin: Optional[str] = None
    supplier_id: Optional[int] = None
    note:Optional[str] = None

class YarnResponse(YarnBase):
    yarn_id: int
    class Config:
        from_attributes = True