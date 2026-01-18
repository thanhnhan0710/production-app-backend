from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models.machine import Machine, MachineStatus, MachineArea
from app.schemas.machine_schema import MachineCreate, MachineUpdate
from app.models.machine_log import MachineLog


# =========================
# GET LIST
# =========================
def get_machines(
    db: Session,
    skip: int = 0,
    limit: int = 100
):
    return (
        db.query(Machine)
        .offset(skip)
        .limit(limit)
        .all()
    )


# =========================
# GET ONE (BY ID)
# =========================
def get_machine(db: Session, machine_id: int):
    return db.get(Machine, machine_id)


# =========================
<<<<<<< HEAD
# SEARCH
=======
# SEARCH (TÊN / MỤC ĐÍCH / TRẠNG THÁI / KHU VỰC)
>>>>>>> c468be65d7388abd40a800c84aa27cfe56d2c0d3
# =========================
def search_machines(
    db: Session,
    keyword: str | None = None,
<<<<<<< HEAD
    status: MachineStatus | None = None,
    area: MachineArea | None = None,
=======
    status: MachineStatus | None = None, # Dùng Enum type hint
    area: MachineArea | None = None,     # Thêm bộ lọc khu vực
>>>>>>> c468be65d7388abd40a800c84aa27cfe56d2c0d3
    skip: int = 0,
    limit: int = 100
):
    query = db.query(Machine)

    # 1. Lọc theo từ khóa (Tên máy hoặc Mục đích sử dụng)
    if keyword:
        keyword_filter = f"%{keyword}%"
        query = query.filter(
            or_(
                Machine.machine_name.ilike(keyword_filter),
                Machine.purpose.ilike(keyword_filter)
            )
        )

    # 2. Lọc theo trạng thái (nếu có)
    if status:
        query = query.filter(Machine.status == status)

<<<<<<< HEAD
=======
    # 3. Lọc theo khu vực (nếu có)
>>>>>>> c468be65d7388abd40a800c84aa27cfe56d2c0d3
    if area:
        query = query.filter(Machine.area == area)

    return (
        query
        .offset(skip)
        .limit(limit)
        .all()
    )


# =========================
# CREATE
# =========================
def create_machine(db: Session, data: MachineCreate):
    # data.model_dump() sẽ tự động convert Enum thành value string tương ứng nếu cần
    machine = Machine(**data.model_dump())
    db.add(machine)
    db.commit()
    db.refresh(machine)
    return machine


# =========================
# UPDATE
# =========================
def update_machine(
    db: Session,
    machine_id: int,
    data: MachineUpdate
):
    machine = get_machine(db, machine_id)
    if not machine:
        return None

    # exclude_unset=True: Chỉ lấy những trường người dùng gửi lên
    update_data = data.model_dump(exclude_unset=True)

    for k, v in update_data.items():
        setattr(machine, k, v)

    db.commit()
    db.refresh(machine)
    return machine


# =========================
# DELETE
# =========================
def delete_machine(db: Session, machine_id: int):
    machine = get_machine(db, machine_id)
    if not machine:
        return False

    db.delete(machine)
    db.commit()
<<<<<<< HEAD
    return True


# =========================
# UPDATE STATUS (SỬA LỖI Ở ĐÂY)
# =========================
def update_machine_status(
    db: Session, 
    machine_id: int, 
    new_status: str, 
    reason: str = None, 
    image_url: str = None
):
    # [SỬA LỖI]: Đổi Machine.id thành Machine.machine_id
    machine = db.query(Machine).filter(Machine.machine_id == machine_id).first()
    
    if not machine:
        return None

    # Nếu trạng thái không đổi thì không cần làm gì
    if machine.status == new_status:
        return machine

    current_time = datetime.now()

    # 2. Tìm log cũ đang mở (end_time là Null) và ĐÓNG NÓ LẠI
    last_log = db.query(MachineLog).filter(
        MachineLog.machine_id == machine_id,
        MachineLog.end_time == None
    ).order_by(MachineLog.start_time.desc()).first()

    if last_log:
        last_log.end_time = current_time

    # 3. TẠO LOG MỚI
    new_log = MachineLog(
        machine_id=machine_id,
        status=new_status,
        start_time=current_time,
        end_time=None, # Đang diễn ra
        reason=reason,
        image_url=image_url
    )
    db.add(new_log)

    # 4. Cập nhật trạng thái hiện tại vào bảng Machine
    machine.status = new_status
    
    db.commit()
    db.refresh(machine)
    return machine


# =========================
# GET HISTORY
# =========================
def get_machine_history(db: Session, machine_id: int, limit: int = 20):
    return db.query(MachineLog)\
        .filter(MachineLog.machine_id == machine_id)\
        .order_by(MachineLog.start_time.desc())\
        .limit(limit)\
        .all()
=======
    return True
>>>>>>> c468be65d7388abd40a800c84aa27cfe56d2c0d3
