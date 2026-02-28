from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models.product_type import ProductType
from app.schemas.product_type_schema import ProductTypeCreate, ProductTypeUpdate

def get_product_types(db: Session, skip: int = 0, limit: int = 100):
    return db.query(ProductType).offset(skip).limit(limit).all()

def create_product_type(db: Session, data: ProductTypeCreate):
    new_type = ProductType(**data.model_dump())
    db.add(new_type)
    db.commit()
    db.refresh(new_type)
    return new_type

def update_product_type(db: Session, type_id: int, data: ProductTypeUpdate):
    pt = db.get(ProductType, type_id)
    if not pt:
        return None
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(pt, k, v)
    db.commit()
    db.refresh(pt)
    return pt

def delete_product_type(db: Session, type_id: int):
    pt = db.get(ProductType, type_id)
    if not pt:
        return False
    db.delete(pt)
    db.commit()
    return True

def search_product_types(db: Session, keyword: str, skip: int = 0, limit: int = 100):
    return (
        db.query(ProductType)
        .filter(
            or_(
                ProductType.type_name.ilike(f"%{keyword}%"),
                ProductType.description.ilike(f"%{keyword}%")
            )
        )
        .offset(skip)
        .limit(limit)
        .all()
    )