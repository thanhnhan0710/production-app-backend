from datetime import datetime
from fastapi import UploadFile
from io import BytesIO
import pandas as pd
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_

# [CẬP NHẬT] Đổi MachineArea thành Area
from app.models.machine import Machine, WeavingMachine, DyeingMachine
from app.models.machine_type import MachineType
from app.models.machine_status import MachineStatus
from app.models.area import Area 
from app.schemas.machine_schema import MachineCreate, MachineUpdate
from app.models.machine_log import MachineLog

def get_machines(db: Session, skip: int = 0, limit: int = 100):
    return (
        db.query(Machine)
        .options(
            joinedload(Machine.machine_type),
            joinedload(Machine.status),
            joinedload(Machine.area)
        )
        .offset(skip)
        .limit(limit)
        .all()
    )

def get_machine(db: Session, machine_id: int):
    return db.query(Machine).options(
        joinedload(Machine.machine_type),
        joinedload(Machine.status),
        joinedload(Machine.area)
    ).filter(Machine.machine_id == machine_id).first()

def search_machines(
    db: Session,
    keyword: str | None = None,
    status_id: int | None = None, 
    area_id: int | None = None, 
    skip: int = 0,
    limit: int = 100
):
    query = db.query(Machine).options(
        joinedload(Machine.machine_type),
        joinedload(Machine.status),
        joinedload(Machine.area)
    )

    if keyword:
        # Tự động JOIN với Area để tìm kiếm theo tên Khu vực
        query = query.outerjoin(MachineType).outerjoin(Area).filter(
            or_(
                Machine.machine_name.ilike(f"%{keyword}%"),
                Machine.serial_number.ilike(f"%{keyword}%"),
                MachineType.type_name.ilike(f"%{keyword}%"),
                Area.area_name.ilike(f"%{keyword}%")
            )
        )

    if status_id:
        query = query.filter(Machine.status_id == status_id)
    if area_id:
        query = query.filter(Machine.area_id == area_id)

    return query.offset(skip).limit(limit).all()

def create_machine(db: Session, data: MachineCreate):
    dump_data = data.model_dump(exclude_none=True)
    poly_type = dump_data.get("polymorphic_type", "base_machine")
    
    if poly_type == "weaving_machine":
        machine = WeavingMachine(**dump_data)
    elif poly_type == "dyeing_machine":
        machine = DyeingMachine(**dump_data)
    else:
        machine = Machine(**dump_data)

    db.add(machine)
    db.commit()
    db.refresh(machine)
    return get_machine(db, machine.machine_id)

def update_machine(db: Session, machine_id: int, data: MachineUpdate):
    machine = db.get(Machine, machine_id)
    if not machine: return None

    update_data = data.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(machine, k, v)

    db.commit()
    db.refresh(machine)
    return get_machine(db, machine_id)

def delete_machine(db: Session, machine_id: int):
    machine = db.get(Machine, machine_id)
    if not machine: return False
    db.delete(machine)
    db.commit()
    return True

def update_machine_status(
    db: Session, machine_id: int, status_name: str, reason: str = None, image_url: str = None
):
    machine = db.get(Machine, machine_id)
    if not machine: return None

    status_record = db.query(MachineStatus).filter(MachineStatus.status_name.ilike(status_name)).first()
    if not status_record:
        status_record = MachineStatus(status_name=status_name)
        db.add(status_record)
        db.flush()

    new_status_id = status_record.status_id
    if machine.status_id == new_status_id: return machine

    current_time = datetime.now()

    last_log = db.query(MachineLog).filter(
        MachineLog.machine_id == machine_id, MachineLog.end_time == None
    ).order_by(MachineLog.start_time.desc()).first()

    if last_log: last_log.end_time = current_time

    new_log = MachineLog(
        machine_id=machine_id, status=status_name, start_time=current_time,
        end_time=None, reason=reason, image_url=image_url
    )
    db.add(new_log)

    machine.status_id = new_status_id
    db.commit()
    return get_machine(db, machine_id)

def get_machine_history(db: Session, machine_id: int, limit: int = 20):
    return db.query(MachineLog).filter(MachineLog.machine_id == machine_id).order_by(MachineLog.start_time.desc()).limit(limit).all()

# EXCEL IMPORT (THÔNG MINH - TỰ ĐỘNG TẠO MASTER DATA)
def import_machines_from_excel(db: Session, file: UploadFile):
    try:
        df = pd.read_excel(file.file, header=1)
        df.columns = df.columns.str.strip()
        df = df.where(pd.notnull(df), None)
    except Exception as e:
        return {"status": False, "message": f"Lỗi đọc file Excel: {str(e)}"}

    success_count = 0
    error_rows = []

    # Cache
    areas_map = {a.area_name.strip().lower(): a.area_id for a in db.query(Area).all()}
    status_map = {s.status_name.strip().lower(): s.status_id for s in db.query(MachineStatus).all()}
    existing_machines = {m.machine_name.strip().lower() for m in db.query(Machine.machine_name).all()}
    excel_current_machines = set()

    for index, row in df.iterrows():
        excel_row_num = index + 3

        machine_name = str(row.get('MACHINE NAME', '')).strip()
        if not machine_name or machine_name == 'None': continue

        machine_name_lower = machine_name.lower()
        if machine_name_lower in existing_machines or machine_name_lower in excel_current_machines:
            error_rows.append(f"Dòng {excel_row_num}: Máy '{machine_name}' đã tồn tại.")
            continue

        excel_current_machines.add(machine_name_lower)

        # Xử lý Khu vực bằng bảng Area
        area_str = str(row.get('AREA', '')).strip()
        area_id = None
        if area_str and area_str != 'None':
            area_key = area_str.lower()
            if area_key not in areas_map:
                new_area = Area(area_name=area_str)
                db.add(new_area)
                db.flush()
                areas_map[area_key] = new_area.area_id
            area_id = areas_map[area_key]

        # Xử lý Trạng thái
        status_str = str(row.get('STATUS', 'STOPPED')).strip()
        status_id = None
        if status_str and status_str != 'None':
            status_key = status_str.lower()
            if status_key not in status_map:
                new_status = MachineStatus(status_name=status_str)
                db.add(new_status)
                db.flush()
                status_map[status_key] = new_status.status_id
            status_id = status_map[status_key]

        try:
            lines_val = row.get('TOTAL LINE')
            total_lines = int(float(lines_val)) if pd.notnull(lines_val) and str(lines_val).strip() != '' else None

            speed_val = row.get('MAX SPEED (round/ minute)')
            speed = int(float(speed_val)) if pd.notnull(speed_val) and str(speed_val).strip() != '' else None

            serial_val = str(row.get('SERI NUMBER', '')).strip()
            serial_number = serial_val if serial_val != 'None' and serial_val != '' else None

            new_machine = WeavingMachine(
                machine_name=machine_name,
                total_lines=total_lines,
                serial_number=serial_number,
                speed=speed,
                area_id=area_id,
                status_id=status_id,
                polymorphic_type="weaving_machine"
            )
            db.add(new_machine)
            success_count += 1
            
        except Exception as e:
            error_rows.append(f"Dòng {excel_row_num}: Lỗi định dạng dữ liệu ({str(e)})")

    db.commit()
    return {"status": True, "success_count": success_count, "errors": error_rows}

def export_machines_to_excel(db: Session):
    machines = db.query(Machine).options(joinedload(Machine.area), joinedload(Machine.status)).all()

    data = []
    for m in machines:
        row_data = {
            "MACHINE NAME": m.machine_name,
            "SERI NUMBER": m.serial_number,
            "AREA": m.area.area_name if m.area else "",
            "STATUS": m.status.status_name if m.status else "",
            "TYPE": m.polymorphic_type
        }
        
        if isinstance(m, WeavingMachine):
            row_data["TOTAL LINE"] = m.total_lines
            row_data["MAX SPEED (round/ minute)"] = m.speed
            row_data["PURPOSE"] = m.purpose

        data.append(row_data)

    df = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Machines')

    output.seek(0)
    return output