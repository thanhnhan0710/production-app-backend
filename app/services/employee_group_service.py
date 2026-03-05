from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models.employee_group import EmployeeGroup
from app.schemas.employee_group_schema import EmployeeGroupCreate, EmployeeGroupUpdate

def get_groups(db: Session, skip: int = 0, limit: int = 100):
    return db.query(EmployeeGroup).offset(skip).limit(limit).all()

def get_groups_by_department(db: Session, department_id: int, skip: int = 0, limit: int = 100):
    return (
        db.query(EmployeeGroup)
        .filter(EmployeeGroup.department_id == department_id)
        .offset(skip)
        .limit(limit)
        .all()
    )

def create_group(db: Session, data: EmployeeGroupCreate):
    db_obj = EmployeeGroup(**data.model_dump())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def update_group(db: Session, group_id: int, data: EmployeeGroupUpdate):
    db_obj = db.get(EmployeeGroup, group_id)
    if not db_obj:
        return None
        
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_obj, key, value)
        
    db.commit()
    db.refresh(db_obj)
    return db_obj

def delete_group(db: Session, group_id: int):
    db_obj = db.get(EmployeeGroup, group_id)
    if not db_obj:
        return False
        
    db.delete(db_obj)
    db.commit()
    return True

def search_groups(db: Session, keyword: str, skip: int = 0, limit: int = 100):
    return (
        db.query(EmployeeGroup)
        .filter(
            or_(
                EmployeeGroup.group_name.ilike(f"%{keyword}%"),
                EmployeeGroup.description.ilike(f"%{keyword}%")
            )
        )
        .offset(skip)
        .limit(limit)
        .all()
    )