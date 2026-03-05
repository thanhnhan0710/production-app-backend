from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List

from app.api import deps
from app.schemas.employee_group_schema import EmployeeGroupResponse, EmployeeGroupCreate, EmployeeGroupUpdate
from app.services import employee_group_service
from app.core.websockets import ws_manager

router = APIRouter()

@router.get("/", response_model=List[EmployeeGroupResponse])
def read_groups(skip: int = 0, limit: int = 100, db: Session = Depends(deps.get_db)):
    return employee_group_service.get_groups(db, skip, limit)

@router.get("/department/{department_id}", response_model=List[EmployeeGroupResponse])
def read_groups_by_dept(department_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(deps.get_db)):
    return employee_group_service.get_groups_by_department(db, department_id, skip, limit)

@router.get("/search", response_model=List[EmployeeGroupResponse])
def search_groups(keyword: str, skip: int = 0, limit: int = 100, db: Session = Depends(deps.get_db)):
    return employee_group_service.search_groups(db, keyword, skip, limit)

@router.post("/", response_model=EmployeeGroupResponse)
def create_group(
    data: EmployeeGroupCreate, 
    background_tasks: BackgroundTasks, 
    db: Session = Depends(deps.get_db)
):
    new_group = employee_group_service.create_group(db, data)
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_EMPLOYEE_GROUPS")
    # Thay đổi tổ có thể ảnh hưởng đến sơ đồ phòng ban
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_DEPARTMENTS")
    return new_group

@router.put("/{group_id}", response_model=EmployeeGroupResponse)
def update_group(
    group_id: int, 
    data: EmployeeGroupUpdate, 
    background_tasks: BackgroundTasks, 
    db: Session = Depends(deps.get_db)
):
    updated_group = employee_group_service.update_group(db, group_id, data)
    if not updated_group:
        raise HTTPException(status_code=404, detail="Employee Group not found")
        
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_EMPLOYEE_GROUPS")
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_EMPLOYEES")
    return updated_group

@router.delete("/{group_id}")
def delete_group(
    group_id: int, 
    background_tasks: BackgroundTasks, 
    db: Session = Depends(deps.get_db)
):
    success = employee_group_service.delete_group(db, group_id)
    if not success:
        raise HTTPException(status_code=404, detail="Employee Group not found")
        
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_EMPLOYEE_GROUPS")
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_EMPLOYEES")
    return {"message": "Deleted successfully"}