from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.api import deps
from app.schemas.weaving_inspection_schema import (
    WeavingInspectionResponse,
    WeavingInspectionCreate,
    WeavingInspectionUpdate
)
from app.services import weaving_inspection_service

router = APIRouter()

# =========================

# GET LIST (All or Filter by Ticket)
# =========================
@router.get("/", response_model=List[WeavingInspectionResponse])
def read_inspections(
    ticket_id: Optional[int] = Query(None, description="Filter by Weaving Basket Ticket ID"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db)
):
    """
    Get list of inspections.
    - If `ticket_id` is provided: Returns inspections for that specific ticket (Sorted by time desc).
    - If `ticket_id` is missing: Returns all inspections (Admin view).
    """
    if ticket_id:
        return weaving_inspection_service.get_inspections_by_ticket(db, ticket_id, skip, limit)
    
    return weaving_inspection_service.get_all_inspections(db, skip, limit)


# =========================
# GET DETAIL
# =========================
@router.get("/{inspection_id}", response_model=WeavingInspectionResponse)
def read_inspection(
    inspection_id: int,
    db: Session = Depends(deps.get_db)
):
    """
    Get specific inspection details by ID.
    """
    inspection = weaving_inspection_service.get_inspection_by_id(db, inspection_id)
    if not inspection:
        raise HTTPException(status_code=404, detail="Inspection record not found")
    return inspection


# =========================
# CREATE
# =========================
@router.post("/", response_model=WeavingInspectionResponse)
def create_inspection(
    inspection_in: WeavingInspectionCreate,
    db: Session = Depends(deps.get_db)
):
    """
    Record a new quality inspection (e.g., 'Lan 1', 'Ra ro').
    """
    # Service will check if ticket_id exists (raises 404 if not)
    return weaving_inspection_service.create_inspection(db, inspection_in)


# =========================
# UPDATE
# =========================
@router.put("/{inspection_id}", response_model=WeavingInspectionResponse)
def update_inspection(
    inspection_id: int,
    inspection_in: WeavingInspectionUpdate,
    db: Session = Depends(deps.get_db)
):
    """
    Update inspection results (e.g., correcting measurement data).
    """
    return weaving_inspection_service.update_inspection(db, inspection_id, inspection_in)


# =========================
# DELETE
# =========================
@router.delete("/{inspection_id}")
def delete_inspection(
    inspection_id: int,
    db: Session = Depends(deps.get_db)
):
    """
    Delete an inspection record.
    """
    return weaving_inspection_service.delete_inspection(db, inspection_id)