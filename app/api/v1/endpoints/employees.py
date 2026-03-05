from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session
from typing import List
from app.core.websockets import ws_manager # Import WebSocket
from fastapi.responses import StreamingResponse
from app.api import deps
from app.schemas.employee_schema import EmployeeResponse, EmployeeCreate, EmployeeUpdate
from app.services import employee_service

router = APIRouter()

@router.get("/", response_model=List[EmployeeResponse])
def read_employees(skip: int = 0, limit: int = 100, db: Session = Depends(deps.get_db)):
    return employee_service.get_employees(db, skip=skip, limit=limit)

@router.post("/", response_model=EmployeeResponse)
def create_employee(
    emp: EmployeeCreate, 
    background_tasks: BackgroundTasks, # [MỚI] Thêm BackgroundTasks
    db: Session = Depends(deps.get_db)
):
    new_emp = employee_service.create_employee(db, emp)
    
    # [MỚI] Bắn tín hiệu WebSocket
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_EMPLOYEES")
    return new_emp

# Endpoint tìm theo mã bộ phận
@router.get("/department/{department_id}", response_model=List[EmployeeResponse])
def read_employees_by_department(
    department_id: int,
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(deps.get_db)
):
    return employee_service.get_employees_by_department(db, department_id, skip, limit)

@router.get("/count", response_model=int)
def get_employee_count(db: Session = Depends(deps.get_db)):
    return employee_service.count_employees(db)

@router.get("/group/{group_id}", response_model=List[EmployeeResponse])
def read_employees_by_group(
    group_id: int,
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(deps.get_db)
):
    return employee_service.get_employees_by_group(db, group_id, skip, limit)

@router.put("/{emp_id}", response_model=EmployeeResponse)
def update_employee(
    emp_id: int, 
    emp: EmployeeUpdate, 
    background_tasks: BackgroundTasks, # [MỚI] Thêm BackgroundTasks
    db: Session = Depends(deps.get_db)
):
    updated_emp = employee_service.update_employee(db, emp_id, emp)
    if not updated_emp:
        raise HTTPException(status_code=404, detail="Employee not found")
        
    # [MỚI] Bắn tín hiệu WebSocket
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_EMPLOYEES")
    return updated_emp

@router.delete("/{emp_id}")
def delete_employee(
    emp_id: int, 
    background_tasks: BackgroundTasks, # [MỚI] Thêm BackgroundTasks
    db: Session = Depends(deps.get_db)
):
    success = employee_service.delete_employee(db, emp_id)
    if not success:
        raise HTTPException(status_code=404, detail="Employee not found")
        
    # [MỚI] Bắn tín hiệu WebSocket
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_EMPLOYEES")
    return {"message": "Deleted successfully"}

@router.get("/search", response_model=List[EmployeeResponse])
def search_employees(
    keyword: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db)
):
    return employee_service.search_employees(db, keyword, skip, limit)

# =========================
# IMPORT EXCEL
# =========================
@router.post("/import", status_code=200)
def import_excel(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(deps.get_db)
):
    """
    Upload file Excel để import danh sách Nhân viên.
    Tự động tạo mới Phòng ban nếu phòng ban trong file chưa tồn tại.
    """
    if not file.filename.endswith(('.xls', '.xlsx')):
        raise HTTPException(status_code=400, detail="Chỉ chấp nhận định dạng .xls hoặc .xlsx")
        
    result = employee_service.import_employees_from_excel(db, file)
    
    if result.get("status"):
        if result.get("success_count", 0) > 0:
            # Bắn tín hiệu để UI tự động tải lại cả 2 danh sách
            background_tasks.add_task(ws_manager.broadcast, "REFRESH_EMPLOYEES")
            background_tasks.add_task(ws_manager.broadcast, "REFRESH_DEPARTMENTS")
        return result
    else:
        raise HTTPException(status_code=400, detail=result.get("message"))

# =========================
# EXPORT EXCEL
# =========================
@router.get("/export", status_code=200)
def export_excel(db: Session = Depends(deps.get_db)):
    """
    Tải xuống file Excel danh sách nhân viên.
    """
    output = employee_service.export_employees_to_excel(db)
    
    headers = {
        'Content-Disposition': 'attachment; filename="Employees.xlsx"'
    }
    
    return StreamingResponse(
        output, 
        headers=headers, 
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )