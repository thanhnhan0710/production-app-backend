from datetime import datetime
from fastapi import UploadFile
import pandas as pd
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
    return True


# =========================
# UPDATE STATUS (LOGIC QUAN TRỌNG - GIỮ LẠI TỪ HEAD)
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

# =========================
# GET BY NAME (Tiện ích check trùng)
# =========================
def get_machine_by_name(db: Session, machine_name: str):
    return db.query(Machine).filter(Machine.machine_name == machine_name).first()

# =========================
# EXCEL IMPORT
# =========================
def import_machines_from_excel(db: Session, file: UploadFile):
    try:
        # header=1 vì dòng 1 là Title "Thông tin máy dệt cơ bản", dòng 2 mới là cột
        df = pd.read_excel(file.file, header=1)
        df = df.where(pd.notnull(df), None)
    except Exception as e:
        return {"status": False, "message": f"Lỗi đọc file Excel: {str(e)}"}

    success_count = 0
    error_rows = []

    # Lấy danh sách các giá trị hợp lệ của Khu vực (Enum)
    valid_areas = [e.value for e in MachineArea]

    for index, row in df.iterrows():
        excel_row_num = index + 3 # Dòng thực tế trên file Excel

        machine_name = str(row.get('MACHINE NAME', '')).strip()
        if not machine_name or machine_name == 'None':
            continue

        # 1. Kiểm tra trùng lặp tên máy
        if get_machine_by_name(db, machine_name):
            error_rows.append(f"Dòng {excel_row_num}: Máy '{machine_name}' đã tồn tại.")
            continue

        # 2. Xử lý Enum Khu Vực
        area_str = str(row.get('AREA', '')).strip()
        area_val = area_str if area_str in valid_areas else None

        # 3. Ép kiểu dữ liệu an toàn
        try:
            lines_val = row.get('TOTAL LINE')
            total_lines = int(float(lines_val)) if pd.notnull(lines_val) and str(lines_val).strip() != '' else None

            speed_val = row.get('MAX SPEED (round/ minute)')
            speed = int(float(speed_val)) if pd.notnull(speed_val) and str(speed_val).strip() != '' else None

            serial_val = str(row.get('SERI NUMBER', '')).strip()
            serial_number = serial_val if serial_val != 'None' and serial_val != '' else None

            # 4. Insert DB
            new_machine = Machine(
                machine_name=machine_name,
                total_lines=total_lines,
                serial_number=serial_number,
                speed=speed,
                area=area_val,
                status=MachineStatus.STOPPED # Mặc định máy mới là STOPPED
            )
            db.add(new_machine)
            success_count += 1
            
        except Exception as e:
            error_rows.append(f"Dòng {excel_row_num}: Lỗi định dạng dữ liệu ({str(e)})")

    db.commit()
    
    return {
        "status": True, 
        "success_count": success_count, 
        "errors": error_rows
    }