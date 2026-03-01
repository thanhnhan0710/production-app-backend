from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models.machine_status import MachineStatus
from app.schemas.machine_status_schema import MachineStatusCreate, MachineStatusUpdate

def get_machine_statuses(db: Session, skip: int = 0, limit: int = 100):
    return db.query(MachineStatus).offset(skip).limit(limit).all()

def search_machine_statuses(db: Session, keyword: str, skip: int = 0, limit: int = 100):
    return db.query(MachineStatus).filter(
        or_(
            MachineStatus.status_name.ilike(f"%{keyword}%"),
            MachineStatus.description.ilike(f"%{keyword}%")
        )
    ).offset(skip).limit(limit).all()

def create_machine_status(db: Session, data: MachineStatusCreate):
    new_status = MachineStatus(**data.model_dump())
    db.add(new_status)
    db.commit()
    db.refresh(new_status)
    return new_status

def update_machine_status(db: Session, status_id: int, data: MachineStatusUpdate):
    ms = db.get(MachineStatus, status_id)
    if not ms:
        return None
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(ms, k, v)
    db.commit()
    db.refresh(ms)
    return ms

def delete_machine_status(db: Session, status_id: int):
    ms = db.get(MachineStatus, status_id)
    if not ms:
        return False
    db.delete(ms)
    db.commit()
    return True