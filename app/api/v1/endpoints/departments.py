from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.api import deps
from app.schemas.department_schema import DepartmentResponse, DepartmentCreate, DepartmentUpdate
from app.services import department_service

router = APIRouter()

@router.get("/", response_model=List[DepartmentResponse])
def read_departments(skip: int = 0, limit: int = 100, db: Session = Depends(deps.get_db)):
    return department_service.get_departments(db, skip=skip, limit=limit)

@router.post("/", response_model=DepartmentResponse)
def create_department(dept: DepartmentCreate, db: Session = Depends(deps.get_db)):
    return department_service.create_department(db, dept)

@router.put("/{dept_id}", response_model=DepartmentResponse)
def update_department(dept_id: int, dept: DepartmentUpdate, db: Session = Depends(deps.get_db)):
    updated_dept = department_service.update_department(db, dept_id, dept)
    if not updated_dept:
        raise HTTPException(status_code=404, detail="Department not found")
    return updated_dept

@router.delete("/{dept_id}")
def delete_department(dept_id: int, db: Session = Depends(deps.get_db)):
    success = department_service.delete_department(db, dept_id)
    if not success:
        raise HTTPException(status_code=404, detail="Department not found")
    return {"message": "Deleted successfully"}

@router.get("/search", response_model=List[DepartmentResponse])
def search_departments(
    keyword: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db)
):
    return department_service.search_departments(db, keyword, skip, limit)
