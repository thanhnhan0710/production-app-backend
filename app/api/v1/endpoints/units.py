from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from app.api import deps
from app.schemas.unit_schema import (
    UnitResponse,
    UnitCreate,
    UnitUpdate
)
from app.services import unit_service

router = APIRouter()

@router.get("/", response_model=List[UnitResponse])
def read_units(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db)
):
    return unit_service.get_units(db, skip=skip, limit=limit)

@router.post("/", response_model=UnitResponse)
def create_unit(
    data: UnitCreate,
    db: Session = Depends(deps.get_db)
):
    return unit_service.create_unit(db, data)

@router.put("/{unit_id}", response_model=UnitResponse)
def update_unit(
    unit_id: int,
    data: UnitUpdate,
    db: Session = Depends(deps.get_db)
):
    unit = unit_service.update_unit(db, unit_id, data)
    if not unit:
        raise HTTPException(
            status_code=404,
            detail="Unit not found"
        )
    return unit


@router.delete("/{unit_id}")
def delete_unit(
    unit_id: int,
    db: Session = Depends(deps.get_db)
):
    success = unit_service.delete_unit(db, unit_id)
    if not success:
        raise HTTPException(
            status_code=404,
            detail="Unit not found"
        )
    return {"message": "Deleted successfully"}

@router.get("/search", response_model=List[UnitResponse])
def search_units(
    keyword: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db)
):
    return unit_service.search_units(db, keyword, skip, limit)