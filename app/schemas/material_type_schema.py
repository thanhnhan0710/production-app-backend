from pydantic import BaseModel, Field
from typing import Optional

class MaterialTypeBase(BaseModel):
    type_name: str = Field(..., description="Tên loại nguyên vật liệu")
    description: Optional[str] = None

class MaterialTypeCreate(MaterialTypeBase):
    pass

class MaterialTypeUpdate(BaseModel):
    type_name: Optional[str] = None
    description: Optional[str] = None

class MaterialTypeResponse(MaterialTypeBase):
    type_id: int

    class Config:
        from_attributes = True