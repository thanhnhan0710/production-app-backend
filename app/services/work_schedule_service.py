from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, func, extract
from fastapi import HTTPException
from typing import Optional
from datetime import date

from app.models.work_schedule import WorkSchedule 
from app.schemas.work_schedule_schema import WorkScheduleCreate, WorkScheduleUpdate

# ============================
# READ (Get Data)
# ============================

def get_schedule_by_id(db: Session, schedule_id: int):
    return db.query(WorkSchedule).filter(WorkSchedule.id == schedule_id).first()

def check_existing_schedule(db: Session, employee_id: int, work_date: date):
    return db.query(WorkSchedule).filter(
        WorkSchedule.employee_id == employee_id,
        WorkSchedule.work_date == work_date
    ).first()

def get_monthly_overtime(db: Session, employee_id: int, year: int, month: int, exclude_schedule_id: Optional[int] = None):
    """[MỚI] Hàm tính tổng số giờ tăng ca của 1 nhân viên trong 1 tháng cụ thể"""
    query = db.query(func.sum(WorkSchedule.overtime_hours)).filter(
        WorkSchedule.employee_id == employee_id,
        extract('year', WorkSchedule.work_date) == year,
        extract('month', WorkSchedule.work_date) == month
    )
    if exclude_schedule_id:
        query = query.filter(WorkSchedule.id != exclude_schedule_id)
        
    result = query.scalar()
    return result or 0.0

def get_schedules(db: Session, skip: int = 0, limit: int = 100):
    return db.query(WorkSchedule).order_by(desc(WorkSchedule.work_date)).offset(skip).limit(limit).all()

def search_schedules(
    db: Session,
    employee_id: Optional[int] = None,
    shift_id: Optional[int] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    skip: int = 0,
    limit: int = 100
):
    query = db.query(WorkSchedule)
    if employee_id:
        query = query.filter(WorkSchedule.employee_id == employee_id)
    if shift_id:
        query = query.filter(WorkSchedule.shift_id == shift_id)
    if from_date:
        query = query.filter(WorkSchedule.work_date >= from_date)
    if to_date:
        query = query.filter(WorkSchedule.work_date <= to_date)

    return query.order_by(desc(WorkSchedule.work_date)).offset(skip).limit(limit).all()


# ============================
# CREATE & UPDATE
# ============================

def create_schedule(db: Session, schedule_in: WorkScheduleCreate):
    # 1. Tránh trùng lịch
    existing = check_existing_schedule(db, schedule_in.employee_id, schedule_in.work_date)
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Trùng lặp: Nhân viên ID {schedule_in.employee_id} đã có lịch ngày {schedule_in.work_date}."
        )

    # 2. [MỚI] Validate Tăng ca <= 40h/tháng
    new_ot = schedule_in.overtime_hours or 0.0
    if new_ot > 0:
        current_monthly_ot = get_monthly_overtime(db, schedule_in.employee_id, schedule_in.work_date.year, schedule_in.work_date.month)
        if current_monthly_ot + new_ot > 40:
            raise HTTPException(
                status_code=400, 
                detail=f"Giới hạn OT: Đã có {current_monthly_ot}h tăng ca tháng {schedule_in.work_date.month}. Không thể thêm {new_ot}h (Max 40h/tháng)."
            )

    # 3. Create
    db_schedule = WorkSchedule(**schedule_in.model_dump())
    db.add(db_schedule)
    db.commit()
    db.refresh(db_schedule)
    
    return db_schedule

def update_schedule(db: Session, schedule_id: int, schedule_in: WorkScheduleUpdate):
    db_schedule = get_schedule_by_id(db, schedule_id)
    if not db_schedule:
        raise HTTPException(status_code=404, detail="Không tìm thấy lịch")

    new_emp_id = schedule_in.employee_id or db_schedule.employee_id
    new_date = schedule_in.work_date or db_schedule.work_date
    
    if (new_emp_id != db_schedule.employee_id) or (new_date != db_schedule.work_date):
        conflict = check_existing_schedule(db, new_emp_id, new_date)
        if conflict and conflict.id != schedule_id:
             raise HTTPException(status_code=409, detail=f"Trùng lặp: Lịch ngày {new_date} đã tồn tại.")

    # [MỚI] Validate Tăng ca <= 40h/tháng khi Update
    new_ot = schedule_in.overtime_hours if schedule_in.overtime_hours is not None else db_schedule.overtime_hours
    if new_ot > 0:
        current_monthly_ot = get_monthly_overtime(db, new_emp_id, new_date.year, new_date.month, exclude_schedule_id=schedule_id)
        if current_monthly_ot + new_ot > 40:
            raise HTTPException(
                status_code=400, 
                detail=f"Giới hạn OT: Đã có {current_monthly_ot}h tăng ca tháng {new_date.month}. Không thể cập nhật thành {new_ot}h (Max 40h/tháng)."
            )

    update_data = schedule_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_schedule, field, value)

    db.commit()
    db.refresh(db_schedule)
    return db_schedule

# ============================
# DELETE
# ============================

def delete_schedule(db: Session, schedule_id: int):
    db_schedule = get_schedule_by_id(db, schedule_id)
    if not db_schedule:
        raise HTTPException(status_code=404, detail="Không tìm thấy lịch")

    db.delete(db_schedule)
    db.commit()
    return {"message": "Work schedule deleted successfully"}