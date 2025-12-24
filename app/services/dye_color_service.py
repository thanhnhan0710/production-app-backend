from sqlalchemy.orm import Session
from sqlalchemy import desc, or_
from fastapi import HTTPException
from typing import Optional, List

# Import Model và Schema
from app.models.dye_color import DyeColor 
from app.schemas.dye_color_schema import DyeColorCreate, DyeColorUpdate

# ============================
# READ (Get Data)
# ============================

def get_dye_color_by_id(db: Session, color_id: int):
    """Get dye color details by ID"""
    return db.query(DyeColor).filter(DyeColor.color_id == color_id).first()

def get_dye_color_by_hex(db: Session, hex_code: str):
    """Get dye color by Hex Code (Used for checking duplicates)"""
    return db.query(DyeColor).filter(DyeColor.hex_code == hex_code).first()

def get_dye_colors(db: Session, skip: int = 0, limit: int = 100):
    """Get list of all dye colors (Sorted by ID desc)"""
    return (
        db.query(DyeColor)
        .order_by(desc(DyeColor.color_id))
        .offset(skip)
        .limit(limit)
        .all()
    )

# ============================
# SEARCH
# ============================

def search_dye_colors(
    db: Session,
    keyword: Optional[str] = None, # Search by Name or Hex
    skip: int = 0,
    limit: int = 100
):
    """
    Search dye colors by Name or Hex Code
    """
    query = db.query(DyeColor)

    if keyword:
        search_term = f"%{keyword}%"
        # Tìm kiếm trong tên màu HOẶC mã hex
        query = query.filter(
            or_(
                DyeColor.color_name.ilike(search_term),
                DyeColor.hex_code.ilike(search_term)
            )
        )

    return query.order_by(desc(DyeColor.color_id)).offset(skip).limit(limit).all()

# ============================
# CREATE
# ============================

def create_dye_color(db: Session, color_in: DyeColorCreate):
    # 1. Check for duplicate Hex Code (Only if hex_code is provided)
    if color_in.hex_code:
        existing_color = get_dye_color_by_hex(db, color_in.hex_code)
        if existing_color:
            raise HTTPException(
                status_code=409,
                detail=f"Hex code '{color_in.hex_code}' already exists."
            )

    # 2. Create object
    db_color = DyeColor(**color_in.model_dump())
    
    # 3. Save to DB
    db.add(db_color)
    db.commit()
    db.refresh(db_color)
    
    return db_color

# ============================
# UPDATE
# ============================

def update_dye_color(db: Session, color_id: int, color_in: DyeColorUpdate):
    # 1. Find the color
    db_color = get_dye_color_by_id(db, color_id)
    if not db_color:
        raise HTTPException(status_code=404, detail="Dye color not found")

    # 2. Check duplicate Hex Code if changed
    if color_in.hex_code and color_in.hex_code != db_color.hex_code:
        existing_hex = get_dye_color_by_hex(db, color_in.hex_code)
        if existing_hex:
            raise HTTPException(
                status_code=409, 
                detail=f"Hex code '{color_in.hex_code}' already exists in another color."
            )

    # 3. Update fields
    update_data = color_in.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(db_color, field, value)

    db.commit()
    db.refresh(db_color)
    return db_color

# ============================
# DELETE
# ============================

def delete_dye_color(db: Session, color_id: int):
    # 1. Find the color
    db_color = get_dye_color_by_id(db, color_id)
    if not db_color:
        raise HTTPException(status_code=404, detail="Dye color not found")

    
   
    if db_color.standards:
        raise HTTPException(
              status_code=400,
             detail="Cannot delete this color because it is used in Standards."
         )

    # 3. Delete
    db.delete(db_color)
    db.commit()
    return {"message": "Dye color deleted successfully"}