from pydantic import BaseModel
from datetime import date
from typing import Optional

class YarnLotBase(BaseModel):
    import_date: date
    total_kg: float
    roll_count: int

    warehouse_location: Optional[str] = None
    container_code: Optional[str] = None

    driver_id: Optional[int] = None
    receiver_id: int
    updated_by: int

class YarnLotCreate(YarnLotBase):
    lot_code: str
    yarn_id: int

class YarnLotUpdate(BaseModel):
    import_date: Optional[date] = None

    total_kg: Optional[float] = None
    roll_count: Optional[int] = None

    warehouse_location: Optional[str] = None
    container_code: Optional[str] = None

    driver_id: Optional[int] = None
    receiver_id: Optional[int] = None
    updated_by: Optional[int] = None


class YarnLotResponse(YarnLotCreate):
    class Config:
        from_attributes = True  # Pydantic v2

class EmployeeShort(BaseModel):
    employee_id: int
    full_name: str

    class Config:
        from_attributes = True


class YarnLotDetail(YarnLotResponse):
    driver: Optional[EmployeeShort]
    receiver: EmployeeShort
    updater: EmployeeShort
