from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.api import deps
from app.schemas.dye_color_schema import (
    DyeColorResponse,
    DyeColorCreate,
    DyeColorUpdate
)
from app.services import dye_color_service

router = APIRouter()

# =========================
# GET LIST
# =========================
@router.get("/", response_model=List[DyeColorResponse])
def read_dye_colors(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db)
):
    """
    Get list of dye colors (with pagination).
    """
    return dye_color_service.get_dye_colors(db, skip, limit)


# =========================
# SEARCH
# =========================
@router.get("/search", response_model=List[DyeColorResponse])
def search_dye_colors(
    keyword: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db)
):
    """
    Search dye colors by Name or Hex Code.
    """
    return dye_color_service.search_dye_colors(
        db=db,
        keyword=keyword,
        skip=skip,
        limit=limit
    )


# =========================
# GET DETAIL
# =========================
@router.get("/{color_id}", response_model=DyeColorResponse)
def read_dye_color(
    color_id: int,
    db: Session = Depends(deps.get_db)
):
    """
    Get specific dye color details by ID.
    """
    color = dye_color_service.get_dye_color_by_id(db, color_id)
    if not color:
        raise HTTPException(status_code=404, detail="Dye color not found")
    return color


# =========================
# CREATE
# =========================
@router.post("/", response_model=DyeColorResponse)
def create_dye_color(
    color_in: DyeColorCreate,
    db: Session = Depends(deps.get_db)
):
    """
    Create a new dye color. Checks for duplicate Hex Code.
    """
    return dye_color_service.create_dye_color(db, color_in)


# =========================
# UPDATE
# =========================
@router.put("/{color_id}", response_model=DyeColorResponse)
def update_dye_color(
    color_id: int,
    color_in: DyeColorUpdate,
    db: Session = Depends(deps.get_db)
):
    """
    Update dye color info. Checks for duplicate Hex Code if changed.
    """
    # Service raises HTTPException 404 or 409 internally
    return dye_color_service.update_dye_color(db, color_id, color_in)


# =========================
# DELETE
# =========================
@router.delete("/{color_id}")
def delete_dye_color(
    color_id: int,
    db: Session = Depends(deps.get_db)
):
    """
    Delete a dye color.
    """
    return dye_color_service.delete_dye_color(db, color_id)