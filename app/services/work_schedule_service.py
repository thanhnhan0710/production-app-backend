from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from fastapi import HTTPException
from typing import Optional
from datetime import date

# Import Model & Schema
from app.models.work_schedule import WorkSchedule # Nhớ sửa đường dẫn đúng file model
from app.schemas.work_schedule_schema import WorkScheduleCreate, WorkScheduleUpdate

# ============================
# READ (Get Data)
# ============================

def get_schedule_by_id(db: Session, schedule_id: int):
    """Get schedule details by ID"""
    return db.query(WorkSchedule).filter(WorkSchedule.id == schedule_id).first()

def check_existing_schedule(db: Session, employee_id: int, work_date: date):
    """
    Helper: Check if an employee already has a schedule on a specific date.
    Used to prevent double-booking.
    """
    return db.query(WorkSchedule).filter(
        WorkSchedule.employee_id == employee_id,
        WorkSchedule.work_date == work_date
    ).first()

def get_schedules(db: Session, skip: int = 0, limit: int = 100):
    """Get list of schedules (Sorted by Date desc)"""
    return (
        db.query(WorkSchedule)
        .order_by(desc(WorkSchedule.work_date))
        .offset(skip)
        .limit(limit)
        .all()
    )



def search_schedules(
    db: Session,
    employee_id: Optional[int] = None,
    shift_id: Optional[int] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    skip: int = 0,
    limit: int = 100
):
    """
    Advanced search for work schedules
    """
    query = db.query(WorkSchedule)

    if employee_id:
        query = query.filter(WorkSchedule.employee_id == employee_id)

    if shift_id:
        query = query.filter(WorkSchedule.shift_id == shift_id)

    if from_date:
        query = query.filter(WorkSchedule.work_date >= from_date)
        
    if to_date:
        query = query.filter(WorkSchedule.work_date <= to_date)

    # Sort: Mới nhất lên đầu
    return query.order_by(desc(WorkSchedule.work_date)).offset(skip).limit(limit).all()



def create_schedule(db: Session, schedule_in: WorkScheduleCreate):
    # 1. Validate: Employee cannot work 2 shifts on the same day (Business Rule)
    # Nếu logic cty bạn cho phép làm 2 ca/ngày thì bỏ đoạn check này đi.
    existing = check_existing_schedule(db, schedule_in.employee_id, schedule_in.work_date)
    
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Employee ID {schedule_in.employee_id} is already scheduled on {schedule_in.work_date}."
        )

    # 2. Check FK validity (Optional but good practice)
    # Bạn có thể check xem employee_id và shift_id có tồn tại thật không ở đây 
    # nếu muốn báo lỗi rõ ràng hơn lỗi của DB.

    # 3. Create
    db_schedule = WorkSchedule(**schedule_in.model_dump())
    
    db.add(db_schedule)
    db.commit()
    db.refresh(db_schedule)
    
    return db_schedule

# ============================
# UPDATE
# ============================

def update_schedule(db: Session, schedule_id: int, schedule_in: WorkScheduleUpdate):
    # 1. Find schedule
    db_schedule = get_schedule_by_id(db, schedule_id)
    if not db_schedule:
        raise HTTPException(status_code=404, detail="Work schedule not found")

    # 2. Validate Conflict (If changing employee or date)
    # Nếu người dùng đổi ngày hoặc đổi nhân viên, phải check xem có bị trùng lịch với record khác không
    new_emp_id = schedule_in.employee_id or db_schedule.employee_id
    new_date = schedule_in.work_date or db_schedule.work_date
    
    # Chỉ check nếu có sự thay đổi về ngày hoặc người
    if (new_emp_id != db_schedule.employee_id) or (new_date != db_schedule.work_date):
        conflict = check_existing_schedule(db, new_emp_id, new_date)
        # Nếu tìm thấy trùng, và cái trùng đó KHÔNG PHẢI là chính bản ghi đang sửa
        if conflict and conflict.id != schedule_id:
             raise HTTPException(
                status_code=409,
                detail=f"Conflict: Employee ID {new_emp_id} is already scheduled on {new_date}."
            )

    # 3. Update
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
        raise HTTPException(status_code=404, detail="Work schedule not found")

    db.delete(db_schedule)
    db.commit()
    return {"message": "Work schedule deleted successfully"}