from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, or_
from fastapi import HTTPException
from typing import Optional, List

from app.models.standard import Standard
from app.models.product import Product
from app.models.dye_color import DyeColor
from app.schemas.standard_schema import StandardCreate, StandardUpdate

# ============================
# READ (Get Data)
# ============================

def get_standard_by_id(db: Session, standard_id: int):
    return (
        db.query(Standard)
        .options(joinedload(Standard.product), joinedload(Standard.dye_color)) # Load quan hệ
        .filter(Standard.standard_id == standard_id)
        .first()
    )

def get_standards(db: Session, skip: int = 0, limit: int = 100):
    return (
        db.query(Standard)
        .options(joinedload(Standard.product), joinedload(Standard.dye_color)) # Load quan hệ
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
    keyword: Optional[str] = None, 
    product_id: Optional[int] = None,
    dye_color_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100
):
    query = db.query(Standard).options(joinedload(Standard.product), joinedload(Standard.dye_color))

    if keyword:
        search_term = f"%{keyword}%"
        # Tìm trong Note, Appearance hoặc Mã sản phẩm, Tên màu
        query = query.join(Product, isouter=True).join(DyeColor, isouter=True).filter(
            or_(
                Standard.note.ilike(search_term),
                Standard.appearance.ilike(search_term),
                # [FIX] Sửa Product.name -> Product.item_code
                Product.item_code.ilike(search_term), 
                DyeColor.color_name.ilike(search_term) 
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
    try:
        db_standard = Standard(**standard_in.model_dump())
        
        db.add(db_standard)
        db.commit()
        db.refresh(db_standard)
        
        return db_standard
    except Exception as e:
        db.rollback()
        print(f"Error creating standard: {str(e)}") 
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# ============================
# UPDATE
# ============================

def update_standard(db: Session, standard_id: int, standard_in: StandardUpdate):
    db_standard = get_standard_by_id(db, standard_id)
    if not db_standard:
        return None

    update_data = standard_in.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(db_standard, field, value)

    try:
        db.commit()
        db.refresh(db_standard)
        return db_standard
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database update error: {str(e)}")

# ============================
# DELETE
# ============================

def delete_standard(db: Session, standard_id: int):
    db_standard = get_standard_by_id(db, standard_id)
    if not db_standard:
        return False

    try:
        db.delete(db_standard)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")