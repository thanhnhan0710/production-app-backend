from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.api import deps
from app.schemas.standard_schema import (
    StandardResponse,
    StandardCreate,
    StandardUpdate
)
from app.services import standard_service

router = APIRouter()

# =========================
# GET LIST
# =========================
@router.get("/", response_model=List[StandardResponse])
def read_standards(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db)
):
    """
    Get list of standards (with pagination).
    """
    return standard_service.get_standards(db, skip, limit)


# =========================
# SEARCH
# =========================
@router.get("/search", response_model=List[StandardResponse])
def search_standards(
    keyword: Optional[str] = None,
    product_id: Optional[int] = None,
    dye_color_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db)
):
    """
    Search standards by Code, Note, Product ID or Dye Color ID.
    """
    return standard_service.search_standards(
        db=db,
        keyword=keyword,
        product_id=product_id,
        dye_color_id=dye_color_id,
        skip=skip,
        limit=limit
    )


# =========================
# GET DETAIL
# =========================
@router.get("/{standard_id}", response_model=StandardResponse)
def read_standard(
    standard_id: int,
    db: Session = Depends(deps.get_db)
):
    """
    Get specific standard details by ID.
    """
    standard = standard_service.get_standard_by_id(db, standard_id)
    if not standard:
        raise HTTPException(status_code=404, detail="Standard not found")
    return standard


# =========================
# CREATE
# =========================
@router.post("/", response_model=StandardResponse)
def create_standard(
    standard_in: StandardCreate,
    db: Session = Depends(deps.get_db)
):
    """
    Create a new standard. Checks for duplicate Code.
    """
    return standard_service.create_standard(db, standard_in)


# =========================
# UPDATE
# =========================
@router.put("/{standard_id}", response_model=StandardResponse)
def update_standard(
    standard_id: int,
    standard_in: StandardUpdate,
    db: Session = Depends(deps.get_db)
):
    """
    Update standard info. Checks for duplicate Code if changed.
    """
    # Service raises HTTPException 404 or 409 internally
    return standard_service.update_standard(db, standard_id, standard_in)


# =========================
# DELETE
# =========================
@router.delete("/{standard_id}")
def delete_standard(
    standard_id: int,
    db: Session = Depends(deps.get_db)
):
    """
    Delete a standard.
    """
    # Service raises HTTPException 404 internally
    return standard_service.delete_standard(db, standard_id)