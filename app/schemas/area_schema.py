from pydantic import BaseModel
from typing import Optional

class AreaBase(BaseModel):
    area_name: str
    description: Optional[str] = None

class AreaCreate(AreaBase):
    pass

class AreaUpdate(BaseModel):
    area_name: Optional[str] = None
    description: Optional[str] = None

class AreaResponse(AreaBase):
    area_id: int

    class Config:
        from_attributes = True