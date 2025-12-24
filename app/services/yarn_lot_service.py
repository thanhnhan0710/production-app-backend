from sqlalchemy.orm import Session
from sqlalchemy import desc
from fastapi import HTTPException

from app.models.yarn_lot import YarnLot
from datetime import date
from typing import Optional, List

from app.schemas.yarn_lot_schema import YarnLotCreate, YarnLotUpdate

# ============================
# READ (Danh sách & Chi tiết)
# ============================

def get_yarn_lots(db: Session, skip: int = 0, limit: int = 100):
    """
    Lấy danh sách lô sợi, mặc định sắp xếp ID giảm dần (mới nhất lên đầu)
    """
    return (
        db.query(YarnLot)
        .order_by(desc(YarnLot.id))
        .offset(skip)
        .limit(limit)
        .all()
    )

def get_yarn_lot_by_id(db: Session, yarn_lot_id: int):
    """
    Lấy chi tiết lô sợi theo ID (Primary Key)
    """
    return db.query(YarnLot).filter(YarnLot.id == yarn_lot_id).first()

def get_yarn_lot_by_code(db: Session, lot_code: str):
    """
    Helper function: Tìm lô sợi theo mã lot_code (Dùng để check unique)
    """
    return db.query(YarnLot).filter(YarnLot.lot_code == lot_code).first()

# ============================
# CREATE
# ============================

def create_yarn_lot(db: Session, lot_data: YarnLotCreate):
    # 1. Kiểm tra lot_code đã tồn tại chưa (Vì lot_code là Unique)
    existing_lot = get_yarn_lot_by_code(db, lot_data.lot_code)
    if existing_lot:
        raise HTTPException(
            status_code=409,
            detail=f"Lot code '{lot_data.lot_code}' already exists."
        )

    # 2. Tạo object mới
    # model_dump() chuyển Pydantic model thành dictionary
    db_lot = YarnLot(**lot_data.model_dump())
    
    db.add(db_lot)
    db.commit()
    db.refresh(db_lot) # Refresh để lấy lại ID vừa sinh ra
    return db_lot

# ============================
# UPDATE
# ============================

def update_yarn_lot(
    db: Session,
    yarn_lot_id: int, 
    lot_data: YarnLotUpdate
):
    # 1. Tìm bản ghi theo ID
    db_lot = get_yarn_lot_by_id(db, yarn_lot_id)
    if not db_lot:
        return None # Hoặc raise HTTPException 404 ở router

    # 2. Kiểm tra nếu người dùng muốn đổi lot_code, xem code mới có trùng không
    if lot_data.lot_code and lot_data.lot_code != db_lot.lot_code:
        existing_code = get_yarn_lot_by_code(db, lot_data.lot_code)
        if existing_code:
             raise HTTPException(
                status_code=409,
                detail=f"Lot code '{lot_data.lot_code}' already exists in another record."
            )

    # 3. Cập nhật dữ liệu
    # exclude_unset=True để chỉ lấy các trường user gửi lên (không lấy field null mặc định)
    update_data = lot_data.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(db_lot, key, value)

    db.commit()
    db.refresh(db_lot)
    return db_lot

# ============================
# DELETE
# ============================

def delete_yarn_lot(db: Session, yarn_lot_id: int):
    db_lot = get_yarn_lot_by_id(db, yarn_lot_id)
    if not db_lot:
        return False

    db.delete(db_lot)
    db.commit()
    return True

# ============================
# SEARCH
# ============================

def search_yarn_lots(
    db: Session,
    lot_code: Optional[str] = None,
    yarn_id: Optional[int] = None,
    container_code: Optional[str] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    note: Optional[str] = None, # Đã sửa từ date -> str
    skip: int = 0,
    limit: int = 100
):
    query = db.query(YarnLot)

    if lot_code:
        # ilike: tìm kiếm không phân biệt hoa thường (Case-insensitive)
        query = query.filter(YarnLot.lot_code.ilike(f"%{lot_code}%"))

    if yarn_id:
        query = query.filter(YarnLot.yarn_id == yarn_id)

    if container_code:
        query = query.filter(YarnLot.container_code.ilike(f"%{container_code}%"))

    if from_date:
        query = query.filter(YarnLot.import_date >= from_date)

    if to_date:
        query = query.filter(YarnLot.import_date <= to_date)
        
    if note:
        query = query.filter(YarnLot.note.ilike(f"%{note}%"))

    # Sắp xếp và phân trang
    return query.order_by(desc(YarnLot.id)).offset(skip).limit(limit).all()