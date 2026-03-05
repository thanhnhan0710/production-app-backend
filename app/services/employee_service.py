import uuid
from io import BytesIO
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, UploadFile
from sqlalchemy import or_, cast
from sqlalchemy import String

from app.models.department import Department
from app.models.employee_group import EmployeeGroup # [MỚI] Import Model Tổ
from app.models.employee import Employee
from app.schemas.employee_schema import EmployeeCreate, EmployeeUpdate


def get_employees(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Employee).offset(skip).limit(limit).all()

def count_employees(db: Session) -> int:
    return db.query(Employee).count()

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

    # Nếu keyword là số -> tìm theo ID / phone
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

def get_employees_by_department(
    db: Session, 
    department_id: int, 
    skip: int = 0, 
    limit: int = 100
):
    return (
        db.query(Employee)
        .filter(Employee.department_id == department_id)
        .offset(skip)
        .limit(limit)
        .all()
    )

# [MỚI] Hàm lấy nhân viên theo mã Tổ
def get_employees_by_group(
    db: Session, 
    group_id: int, 
    skip: int = 0, 
    limit: int = 100
):
    return (
        db.query(Employee)
        .filter(Employee.group_id == group_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


# =========================
# EXCEL IMPORT (NHÂN VIÊN, BỘ PHẬN & TỔ)
# =========================
def import_employees_from_excel(db: Session, file: UploadFile):
    try:
        # header=1 vì dòng 1 là Title "Employee Information", dòng 2 mới là Header
        df = pd.read_excel(file.file, header=1)
        
        # Chuẩn hóa tên cột: xóa khoảng trắng thừa
        df.columns = df.columns.str.strip()
        
        # Thay thế NaN thành None
        df = df.where(pd.notnull(df), None)
    except Exception as e:
        return {"status": False, "message": f"Lỗi đọc file Excel: {str(e)}"}

    success_count = 0
    error_rows = []

    # 1. Cache danh sách phòng ban hiện tại vào Dictionary
    departments = db.query(Department).all()
    dept_dict = {d.department_name.strip().lower(): d for d in departments if d.department_name}

    # 2. Cache danh sách tổ hiện tại
    groups = db.query(EmployeeGroup).all()
    # Group dict có key là tuple: (department_id, group_name) để tránh trùng tên tổ giữa các phòng
    group_dict = {(g.department_id, g.group_name.strip().lower()): g for g in groups if g.group_name}

    for index, row in df.iterrows():
        excel_row_num = index + 3 # Dòng thực tế trên file Excel

        full_name = str(row.get('Name', '')).strip()
        if not full_name or full_name == 'None':
            continue # Bỏ qua dòng trống

        try:
            # --- XỬ LÝ PHÒNG BAN ---
            dept_name_raw = str(row.get('Department', '')).strip()
            dept_name = dept_name_raw if dept_name_raw != 'None' and dept_name_raw else "Chưa phân bổ"
            dept_key = dept_name.lower()
            
            if dept_key not in dept_dict:
                new_dept = Department(department_name=dept_name)
                db.add(new_dept)
                db.flush() 
                dept_dict[dept_key] = new_dept 
                
            department_id = dept_dict[dept_key].department_id

            # --- XỬ LÝ TỔ NHÂN VIÊN ---
            group_name_raw = str(row.get('Group', '')).strip()
            group_id = None
            
            if group_name_raw and group_name_raw != 'nan' and group_name_raw != 'None':
                group_key = (department_id, group_name_raw.lower())
                if group_key not in group_dict:
                    new_group = EmployeeGroup(group_name=group_name_raw, department_id=department_id)
                    db.add(new_group)
                    db.flush()
                    group_dict[group_key] = new_group
                group_id = group_dict[group_key].group_id

            # --- XỬ LÝ DỮ LIỆU NHÂN VIÊN KHÁC ---
            phone_val = row.get('Phone Number')
            if pd.isnull(phone_val) or str(phone_val).strip() in ['', 'nan', 'None']:
                phone = None
            else:
                phone = str(phone_val).split('.')[0].strip()

            email_val = row.get('Email')
            if pd.isnull(email_val) or str(email_val).strip() in ['', 'nan', 'None']:
                email = None
            else:
                email = str(email_val).strip()

            if email is not None:
                existing_emp = db.query(Employee).filter(Employee.email == email).first()
                if existing_emp:
                    error_rows.append(f"Dòng {excel_row_num}: Email '{email}' đã tồn tại trong hệ thống.")
                    continue
                    
            position = str(row.get('Position', '')).strip()
            position = position if position != 'None' and position else None

            note = str(row.get('Note', '')).strip()
            note = note if note != 'None' and note else None

            # --- INSERT NHÂN VIÊN ---
            new_emp = Employee(
                full_name=full_name,
                email=email,
                phone=phone,
                position=position,
                department_id=department_id,
                group_id=group_id, # [MỚI] Bổ sung group_id
                note=note
            )
            
            db.add(new_emp)
            success_count += 1
            
        except Exception as e:
            error_rows.append(f"Dòng {excel_row_num}: Lỗi dữ liệu ({str(e)})")

    db.commit()
    
    return {
        "status": True, 
        "success_count": success_count, 
        "errors": error_rows
    }


# =========================
# EXCEL EXPORT (NHÂN VIÊN)
# =========================
def export_employees_to_excel(db: Session):
    employees = db.query(Employee).all()

    data = []
    for emp in employees:
        dept_name = emp.department.department_name if emp.department else "Chưa phân bổ"
        # [MỚI] Lấy tên tổ
        group_name = emp.group.group_name if emp.group else ""
        
        data.append({
            "Name": emp.full_name,
            "Email": emp.email if emp.email else "",
            "CCCD": "", 
            "Birthday": "", 
            "Phone Number": emp.phone if emp.phone else "",
            "Department": dept_name,
            "Group": group_name, # [MỚI] Xuất cột Group
            "Position": emp.position if emp.position else "",
            "Note": emp.note if emp.note else ""
        })

    df = pd.DataFrame(data)
    
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Employees')

    output.seek(0)
    return output