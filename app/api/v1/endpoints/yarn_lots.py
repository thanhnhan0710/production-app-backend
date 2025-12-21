from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from app.api import deps
from app.schemas.yarn_lot_schema import (
    YarnLotResponse,
    YarnLotCreate,
    YarnLotUpdate
)
from app.services import yarn_lot_service

router = APIRouter()


# =========================
# GET LIST
# =========================
@router.get("/", response_model=List[YarnLotResponse])
def read_yarn_lots(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db)
):
    return yarn_lot_service.get_yarn_lots(db, skip, limit)


# =========================
# SEARCH (ĐA ĐIỀU KIỆN)
# =========================
@router.get("/search", response_model=List[YarnLotResponse])
def search_yarn_lots(
    lot_code: Optional[str] = None,
    yarn_id: Optional[int] = None,
    container_code: Optional[str] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db)
):
    return yarn_lot_service.search_yarn_lots(
        db=db,
        lot_code=lot_code,
        yarn_id=yarn_id,
        container_code=container_code,
        from_date=from_date,
        to_date=to_date,
        skip=skip,
        limit=limit
    )


# =========================
# CREATE
# =========================
@router.post("/", response_model=YarnLotResponse)
def create_yarn_lot(
    lot: YarnLotCreate,
    db: Session = Depends(deps.get_db)
):
    return yarn_lot_service.create_yarn_lot(db, lot)


# =========================
# UPDATE (PK KÉP)
# =========================
@router.put("/{lot_code}/{yarn_id}", response_model=YarnLotResponse)
def update_yarn_lot(
    lot_code: str,
    yarn_id: int,
    lot: YarnLotUpdate,
    db: Session = Depends(deps.get_db)
):
    updated_lot = yarn_lot_service.update_yarn_lot(
        db, lot_code, yarn_id, lot
    )
    if not updated_lot:
        raise HTTPException(
            status_code=404,
            detail="Yarn lot not found"
        )
    return updated_lot


# =========================
# DELETE (PK KÉP)
# =========================
@router.delete("/{lot_code}/{yarn_id}")
def delete_yarn_lot(
    lot_code: str,
    yarn_id: int,
    db: Session = Depends(deps.get_db)
):
    success = yarn_lot_service.delete_yarn_lot(
        db, lot_code, yarn_id
    )
    if not success:
        raise HTTPException(
            status_code=404,
            detail="Yarn lot not found"
        )
    return {"message": "Deleted successfully"}
