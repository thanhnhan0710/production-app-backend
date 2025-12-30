from sqlalchemy.orm import Session
from app.models.material import Material
from app.schemas.material_schema import MaterialCreate, MaterialUpdate
from fastapi import HTTPException
from sqlalchemy import or_

def get_materials(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Material).offset(skip).limit(limit).all()

def get_material(db: Session, material_id: int):
    return db.query(Material).filter(
        Material.material_id == material_id
    ).first()

def create_material(db: Session, material: MaterialCreate):
    db_material = Material(**material.model_dump())
    db.add(db_material)
    db.commit()
    db.refresh(db_material)
    return db_material

def update_material(
    db: Session,
    material_id: int,
    material_data: MaterialUpdate
):
    db_material = get_material(db, material_id)
    if not db_material:
        return None

    update_data = material_data.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(db_material, key, value)

    db.commit()
    db.refresh(db_material)
    return db_material

def delete_material(db: Session, material_id: int):
    db_material = get_material(db, material_id)
    if not db_material:
        return False

    db.delete(db_material)
    db.commit()
    return True


def search_materials(
    db: Session,
    keyword: str,
    skip: int = 0,
    limit: int = 100
):
    query = db.query(Material)

    # Nếu keyword là số → tìm theo ID
    if keyword.isdigit():
        query = query.filter(
            Material.material_id == int(keyword)
        )
    else:
        query = query.filter(
            or_(
                Material.material_name.ilike(f"%{keyword}%"),
                Material.lot_code.ilike(f"%{keyword}%"),
            )
        )

    return (
        query
        .offset(skip)
        .limit(limit)
        .all()
    )
