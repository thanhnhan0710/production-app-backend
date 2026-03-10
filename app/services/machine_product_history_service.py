from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from datetime import datetime

from app.models.machine_product_history import MachineProductHistory
from app.models.machine import Machine
from app.models.product import Product # [THÊM] Import model Product để join và search
from app.schemas.machine_product_history_schema import MachineProductAssign, MachineProductHistoryUpdate

def assign_product_to_machine(db: Session, machine_id: int, data: MachineProductAssign):
    machine = db.query(Machine).filter(Machine.machine_id == machine_id).first()
    if not machine:
        raise ValueError("Máy không tồn tại")
    if machine.polymorphic_type != "weaving_machine":
        raise ValueError("Chỉ có thể gán sản phẩm dệt cho Máy Dệt")

    # [ĐÃ SỬA]: Kiểm tra tồn tại theo machine_id VÀ line_number
    current_running = db.query(MachineProductHistory).filter(
        MachineProductHistory.machine_id == machine_id,
        MachineProductHistory.line_number == data.line_number,
        MachineProductHistory.end_time == None
    ).first()

    if current_running and current_running.product_id == data.product_id:
        return current_running

    if current_running:
        current_running.end_time = datetime.now()
        db.add(current_running)

    new_assignment = MachineProductHistory(
        machine_id=machine_id,
        product_id=data.product_id,
        line_number=data.line_number, # [MỚI]
        notes=data.notes
    )
    db.add(new_assignment)
    db.commit()
    db.refresh(new_assignment)
    
    return db.query(MachineProductHistory).options(joinedload(MachineProductHistory.product)).filter(MachineProductHistory.id == new_assignment.id).first()

def stop_machine_production(db: Session, machine_id: int, line_number: int):
    # [ĐÃ SỬA]: Dừng theo line_number
    current_running = db.query(MachineProductHistory).filter(
        MachineProductHistory.machine_id == machine_id,
        MachineProductHistory.line_number == line_number,
        MachineProductHistory.end_time == None
    ).first()

    if current_running:
        current_running.end_time = datetime.now()
        db.commit()
        db.refresh(current_running)
        return current_running
    return None
def get_current_product_of_machine(db: Session, machine_id: int):
    # [ĐÃ SỬA QUAN TRỌNG]: Trả về DẠNG LIST (.all()) thay vì .first() vì 1 máy có nhiều line đang chạy
    return db.query(MachineProductHistory)\
             .options(joinedload(MachineProductHistory.product))\
             .filter(
                 MachineProductHistory.machine_id == machine_id,
                 MachineProductHistory.end_time == None
             ).all()

def get_machine_history(db: Session, machine_id: int, skip: int = 0, limit: int = 50):
    return db.query(MachineProductHistory)\
             .options(joinedload(MachineProductHistory.product))\
             .filter(MachineProductHistory.machine_id == machine_id)\
             .order_by(MachineProductHistory.start_time.desc())\
             .offset(skip).limit(limit).all()

# ==========================================
# [MỚI] CÁC HÀM XỬ LÝ SỬA, XÓA, TÌM KIẾM
# ==========================================

def search_machine_history(db: Session, machine_id: int, keyword: str, skip: int = 0, limit: int = 50):
    """Tìm kiếm lịch sử theo tên/mã sản phẩm hoặc ghi chú"""
    query = db.query(MachineProductHistory)\
              .options(joinedload(MachineProductHistory.product))\
              .join(Product)\
              .filter(MachineProductHistory.machine_id == machine_id)
    
    if keyword:
        query = query.filter(
            or_(
                Product.item_code.ilike(f"%{keyword}%"),
                MachineProductHistory.notes.ilike(f"%{keyword}%")
            )
        )
    
    return query.order_by(MachineProductHistory.start_time.desc()).offset(skip).limit(limit).all()

def update_history_record(db: Session, history_id: int, data: MachineProductHistoryUpdate):
    """Sửa đổi một bản ghi lịch sử (Ví dụ chỉnh lại giờ, đổi sản phẩm bị gán nhầm)"""
    record = db.query(MachineProductHistory).filter(MachineProductHistory.id == history_id).first()
    if not record:
        return None
    
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(record, key, value)
        
    db.commit()
    db.refresh(record)
    return db.query(MachineProductHistory).options(joinedload(MachineProductHistory.product)).filter(MachineProductHistory.id == history_id).first()

def delete_history_record(db: Session, history_id: int):
    """Xóa một bản ghi lịch sử bị gán nhầm"""
    record = db.query(MachineProductHistory).filter(MachineProductHistory.id == history_id).first()
    if not record:
        return False
    
    db.delete(record)
    db.commit()
    return True