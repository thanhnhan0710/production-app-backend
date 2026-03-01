from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models.area import Area
from app.schemas.area_schema import AreaCreate, AreaUpdate

def get_areas(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Area).offset(skip).limit(limit).all()

def search_areas(db: Session, keyword: str, skip: int = 0, limit: int = 100):
    return db.query(Area).filter(
        or_(
            Area.area_name.ilike(f"%{keyword}%"),
            Area.description.ilike(f"%{keyword}%")
        )
    ).offset(skip).limit(limit).all()

def create_area(db: Session, data: AreaCreate):
    new_area = Area(**data.model_dump())
    db.add(new_area)
    db.commit()
    db.refresh(new_area)
    return new_area

def update_area(db: Session, area_id: int, data: AreaUpdate):
    area = db.get(Area, area_id)
    if not area:
        return None
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(area, k, v)
    db.commit()
    db.refresh(area)
    return area

def delete_area(db: Session, area_id: int):
    area = db.get(Area, area_id)
    if not area:
        return False
    db.delete(area)
    db.commit()
    return True