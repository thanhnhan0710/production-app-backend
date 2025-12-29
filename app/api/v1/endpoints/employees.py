from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.api import deps
from app.schemas.employee_schema import EmployeeResponse, EmployeeCreate, EmployeeUpdate
from app.services import employee_service

router = APIRouter()

@router.get("/", response_model=List[EmployeeResponse])
def read_employees(skip: int = 0, limit: int = 100, db: Session = Depends(deps.get_db)):
    return employee_service.get_employees(db, skip=skip, limit=limit)

@router.post("/", response_model=EmployeeResponse)
def create_employee(emp: EmployeeCreate, db: Session = Depends(deps.get_db)):
    return employee_service.create_employee(db, emp)

# [MỚI] Endpoint tìm theo mã bộ phận
@router.get("/department/{department_id}", response_model=List[EmployeeResponse])
def read_employees_by_department(
    department_id: int,
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(deps.get_db)
):
    return employee_service.get_employees_by_department(db, department_id, skip, limit)

@router.put("/{emp_id}", response_model=EmployeeResponse)
def update_employee(emp_id: int, emp: EmployeeUpdate, db: Session = Depends(deps.get_db)):
    updated_emp = employee_service.update_employee(db, emp_id, emp)
    if not updated_emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    return updated_emp

@router.delete("/{emp_id}")
def delete_employee(emp_id: int, db: Session = Depends(deps.get_db)):
    success = employee_service.delete_employee(db, emp_id)
    if not success:
        raise HTTPException(status_code=404, detail="Employee not found")
    return {"message": "Deleted successfully"}

@router.get("/search", response_model=List[EmployeeResponse])
def search_employees(
    keyword: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db)
):
    return employee_service.search_employees(db, keyword, skip, limit)