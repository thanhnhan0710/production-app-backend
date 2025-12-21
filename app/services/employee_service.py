from sqlalchemy.orm import Session
from app.models.employee import Employee
from app.schemas.employee_schema import EmployeeCreate, EmployeeUpdate
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from sqlalchemy import or_, cast
from sqlalchemy import String

def get_employees(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Employee).offset(skip).limit(limit).all()

def create_employee(db: Session, employee: EmployeeCreate):
    try:
        db_emp = Employee(**employee.model_dump())
        db.add(db_emp)
        db.commit()
        db.refresh(db_emp)
        return db_emp

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Employee with this email already exists."
        )

def update_employee(db: Session, emp_id: int, emp_data: EmployeeUpdate):
    db_emp = db.get(Employee, emp_id)
    if not db_emp:
        return None

    update_data = emp_data.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(db_emp, key, value)

    db.commit()
    db.refresh(db_emp)
    return db_emp

def delete_employee(db: Session, emp_id: int):
    db_emp = db.get(Employee, emp_id)
    if not db_emp:
        return False

    db.delete(db_emp)
    db.commit()
    return True



def search_employees(
    db: Session,
    keyword: str,
    skip: int = 0,
    limit: int = 100
):
    query = db.query(Employee)

    # Nếu keyword là số → tìm theo ID / phone
    if keyword.isdigit():
        query = query.filter(
            or_(
                Employee.employee_id == int(keyword),
                Employee.phone.ilike(f"%{keyword}%")
            )
        )
    else:
        query = query.filter(
            or_(
                Employee.full_name.ilike(f"%{keyword}%"),
                Employee.email.ilike(f"%{keyword}%"),
                Employee.phone.ilike(f"%{keyword}%"),
                Employee.position.ilike(f"%{keyword}%")
            )
        )

    return (
        query
        .offset(skip)
        .limit(limit)
        .all()
    )
