from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models.machine import Machine, MachineStatus, MachineArea
from app.schemas.machine_schema import MachineCreate, MachineUpdate


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
# SEARCH (TÊN / MỤC ĐÍCH / TRẠNG THÁI / KHU VỰC)
# =========================
def search_machines(
    db: Session,
    keyword: str | None = None,
    status: MachineStatus | None = None, # Dùng Enum type hint
    area: MachineArea | None = None,     # Thêm bộ lọc khu vực
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

    # 3. Lọc theo khu vực (nếu có)
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
# UPDATE (PATCH STYLE)
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
    return True