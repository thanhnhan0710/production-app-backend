from sqlalchemy.orm import Session
from sqlalchemy import desc, or_
from fastapi import HTTPException
from typing import Optional, List

# Import Model & Schema
from app.models.standard import Standard # Nhớ sửa đường dẫn đúng file model
from app.schemas.standard_schema import StandardCreate, StandardUpdate

# ============================
# READ (Get Data)
# ============================

def get_standard_by_id(db: Session, standard_id: int):
    """Get standard details by ID"""
    return db.query(Standard).filter(Standard.standard_id == standard_id).first()

def get_standard_by_code(db: Session, code: str):
    """Get standard by Code (Used for duplicate check)"""
    return db.query(Standard).filter(Standard.code == code).first()

def get_standards(db: Session, skip: int = 0, limit: int = 100):
    """Get list of standards (Sorted by ID desc)"""
    return (
        db.query(Standard)
        .order_by(desc(Standard.standard_id))
        .offset(skip)
        .limit(limit)
        .all()
    )

# ============================
# SEARCH
# ============================

def search_standards(
    db: Session,
    keyword: Optional[str] = None, # Search by Code or Note
    product_id: Optional[int] = None,
    dye_color_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100
):
    """
    Advanced search for standards
    """
    query = db.query(Standard)

    if keyword:
        search_term = f"%{keyword}%"
        query = query.filter(
            or_(
                Standard.code.ilike(search_term),
                Standard.note.ilike(search_term)
            )
        )
    
    if product_id:
        query = query.filter(Standard.product_id == product_id)
        
    if dye_color_id:
        query = query.filter(Standard.dye_color_id == dye_color_id)

    return query.order_by(desc(Standard.standard_id)).offset(skip).limit(limit).all()

# ============================
# CREATE
# ============================

def create_standard(db: Session, standard_in: StandardCreate):
    # 1. Check if Standard Code already exists
    existing_std = get_standard_by_code(db, standard_in.code)
    if existing_std:
        raise HTTPException(
            status_code=409,
            detail=f"Standard code '{standard_in.code}' already exists."
        )

    # 2. (Optional) Check if product_id exists
    # Bạn có thể thêm check Product tồn tại ở đây nếu muốn báo lỗi rõ ràng hơn
    # so với lỗi ForeignKey của Database.

    # 3. Create object
    db_standard = Standard(**standard_in.model_dump())
    
    # 4. Save
    db.add(db_standard)
    db.commit()
    db.refresh(db_standard)
    
    return db_standard

# ============================
# UPDATE
# ============================

def update_standard(db: Session, standard_id: int, standard_in: StandardUpdate):
    # 1. Find the standard
    db_standard = get_standard_by_id(db, standard_id)
    if not db_standard:
        raise HTTPException(status_code=404, detail="Standard not found")

    # 2. Check unique code if changed
    if standard_in.code and standard_in.code != db_standard.code:
        existing_code = get_standard_by_code(db, standard_in.code)
        if existing_code:
            raise HTTPException(
                status_code=409, 
                detail=f"Standard code '{standard_in.code}' already exists."
            )

    # 3. Update fields
    update_data = standard_in.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(db_standard, field, value)

    db.commit()
    db.refresh(db_standard)
    return db_standard

# ============================
# DELETE
# ============================

def delete_standard(db: Session, standard_id: int):
    # 1. Find
    db_standard = get_standard_by_id(db, standard_id)
    if not db_standard:
        raise HTTPException(status_code=404, detail="Standard not found")

    # 2. Delete
    db.delete(db_standard)
    db.commit()
    return {"message": "Standard deleted successfully"}