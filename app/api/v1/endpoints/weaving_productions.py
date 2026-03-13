# app/api/v1/endpoints/weaving_productions.py

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.api import deps
from app.schemas.weaving_production_schema import (
    WeavingProductionResponse,
    WeavingProductionCreate,
    WeavingProductionUpdate,
)
from app.services.weaving_production_service import WeavingProductionService

# Import analytics sub-router
from app.api.v1.endpoints.weaving_production_analytics import (
    router as analytics_router,
)

router = APIRouter()

# Mount analytics endpoints tại /analytics/*
router.include_router(analytics_router, prefix="/analytics", tags=["Weaving Analytics"])


# =========================
# GET LIST
# =========================
@router.get("", response_model=List[WeavingProductionResponse])
@router.get("/", response_model=List[WeavingProductionResponse], include_in_schema=False)
def read_weaving_productions(
    skip: int = 0,
    limit: int = 100,
    weaving_ticket_id: Optional[int] = Query(None),
    db: Session = Depends(deps.get_db),
):
    service = WeavingProductionService(db)
    return service.get_multi(skip=skip, limit=limit, weaving_ticket_id=weaving_ticket_id)


# =========================
# CREATE
# =========================
@router.post("", response_model=WeavingProductionResponse)
@router.post("/", response_model=WeavingProductionResponse, include_in_schema=False)
def create_weaving_production(
    production_in: WeavingProductionCreate,
    db: Session = Depends(deps.get_db),
):
    service = WeavingProductionService(db)
    return service.create(obj_in=production_in)


# =========================
# UPDATE
# =========================
@router.put("/{production_id}", response_model=WeavingProductionResponse)
def update_weaving_production(
    production_id: int,
    production_in: WeavingProductionUpdate,
    db: Session = Depends(deps.get_db),
):
    service = WeavingProductionService(db)
    updated = service.update(production_id=production_id, obj_in=production_in)
    if not updated:
        raise HTTPException(status_code=404, detail="Weaving Production record not found")
    return updated


# =========================
# DELETE
# =========================
@router.delete("/{production_id}")
def delete_weaving_production(
    production_id: int,
    db: Session = Depends(deps.get_db),
):
    service = WeavingProductionService(db)
    if not service.delete(production_id):
        raise HTTPException(status_code=404, detail="Weaving Production record not found")
    return {"message": "Deleted successfully"}


# =========================
# SEARCH
# =========================
@router.get("/search", response_model=List[WeavingProductionResponse])
def search_weaving_productions(
    keyword: Optional[str] = None,
    machine_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db),
):
    service = WeavingProductionService(db)
    return service.search(keyword=keyword, machine_id=machine_id, skip=skip, limit=limit)