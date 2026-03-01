from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models.machine_type import MachineType
from app.schemas.machine_type_schema import MachineTypeCreate, MachineTypeUpdate

def get_machine_types(db: Session, skip: int = 0, limit: int = 100):
    return db.query(MachineType).offset(skip).limit(limit).all()

def search_machine_types(db: Session, keyword: str, skip: int = 0, limit: int = 100):
    return db.query(MachineType).filter(
        or_(
            MachineType.type_name.ilike(f"%{keyword}%"),
            MachineType.description.ilike(f"%{keyword}%")
        )
    ).offset(skip).limit(limit).all()

def create_machine_type(db: Session, data: MachineTypeCreate):
    new_type = MachineType(**data.model_dump())
    db.add(new_type)
    db.commit()
    db.refresh(new_type)
    return new_type

def update_machine_type(db: Session, type_id: int, data: MachineTypeUpdate):
    mt = db.get(MachineType, type_id)
    if not mt:
        return None
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(mt, k, v)
    db.commit()
    db.refresh(mt)
    return mt

def delete_machine_type(db: Session, type_id: int):
    mt = db.get(MachineType, type_id)
    if not mt:
        return False
    db.delete(mt)
    db.commit()
    return True