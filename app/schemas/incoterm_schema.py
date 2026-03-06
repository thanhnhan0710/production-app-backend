from pydantic import BaseModel, ConfigDict
from typing import Optional

class IncotermBase(BaseModel):
    incoterm_code: str
    description: Optional[str] = None

class IncotermCreate(IncotermBase):
    pass

class IncotermUpdate(BaseModel):
    incoterm_code: Optional[str] = None
    description: Optional[str] = None

class IncotermResponse(IncotermBase):
    incoterm_id: int
    
    model_config = ConfigDict(from_attributes=True)