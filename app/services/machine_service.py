from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models.machine import Machine
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
# SEARCH (MÃ / TÊN / TRẠNG THÁI)
# =========================
def search_machines(
    db: Session,
    keyword: str | None = None,
    status: str | None = None,
    skip: int = 0,
    limit: int = 100
):
    query = db.query(Machine)

    if keyword:
        query = query.filter(
            or_(
                Machine.machine_id.ilike(f"%{keyword}%")
                if hasattr(Machine.machine_id, "ilike") else False,
                Machine.machine_name.ilike(f"%{keyword}%")
            )
        )

    if status:
        query = query.filter(Machine.status == status)

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
