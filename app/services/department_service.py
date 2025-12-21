from sqlalchemy.orm import Session
from app.models.department import Department
from app.schemas.department_schema import DepartmentCreate, DepartmentUpdate
from sqlalchemy import or_

def get_departments(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Department).offset(skip).limit(limit).all()

# =========================
# GET ONE
# =========================
def get_department(db: Session, department_id: int):
    return db.get(Department, department_id)

def create_department(db: Session, department: DepartmentCreate):
    db_dept = Department(**department.model_dump())
    db.add(db_dept)
    db.commit()
    db.refresh(db_dept)
    return db_dept


def update_department(db: Session, department_id: int, department_data: DepartmentUpdate):
    db_dept = get_department(db, department_id)
    if not db_dept:
        return None

    update_data = department_data.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(db_dept, key, value)

    db.commit()
    db.refresh(db_dept)
    return db_dept
    

def delete_department(db: Session, department_id: int):
    db_dept = db.get(Department, department_id)
    if not db_dept:
        return False

    db.delete(db_dept)
    db.commit()
    return True


def search_departments(
    db: Session,
    keyword: str,
    skip: int = 0,
    limit: int = 100
):
    return (
        db.query(Department)
        .filter(
            or_(
                Department.department_name.ilike(f"%{keyword}%"),
                Department.description.ilike(f"%{keyword}%")
            )
        )
        .offset(skip)
        .limit(limit)
        .all()
    )
