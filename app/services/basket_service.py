import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import desc
from fastapi import HTTPException, UploadFile
from typing import Optional

# Import Model and Schema
from app.models.basket import Basket, BasketStatus
from app.schemas.basket_schema import BasketCreate, BasketUpdate

# ============================
# READ (Get Data)
# ============================

def get_basket_by_id(db: Session, basket_id: int):
    """Get basket details by ID"""
    return db.query(Basket).filter(Basket.basket_id == basket_id).first()

def get_basket_by_code(db: Session, basket_code: str):
    """Get basket details by Code (Used for checking duplicates)"""
    return db.query(Basket).filter(Basket.basket_code == basket_code).first()

def get_baskets(db: Session, skip: int = 0, limit: int = 100):
    """Get list of all baskets (Basic pagination)"""
    return (
        db.query(Basket)
        .order_by(desc(Basket.basket_id))
        .offset(skip)
        .limit(limit)
        .all()
    )

# ============================
# SEARCH (Advanced Search)
# ============================

def search_baskets(
    db: Session,
    keyword: Optional[str] = None,       # Search by Code
    status: Optional[BasketStatus] = None, # Filter by Status
    min_weight: Optional[float] = None,    # Filter by Weight range
    max_weight: Optional[float] = None,
    skip: int = 0,
    limit: int = 100
):
    """
    Search baskets by multiple criteria
    """
    query = db.query(Basket)

    # 1. Search by keyword (Basket Code)
    # Lưu ý: Đã bỏ tìm kiếm theo Supplier vì cột này đã bị xóa khỏi DB
    if keyword:
        search_term = f"%{keyword}%"
        query = query.filter(
            (Basket.basket_code.ilike(search_term)) 
        )

    # 2. Filter by exact status (READY, IN_USE...)
    if status:
        query = query.filter(Basket.status == status)

    # 3. Filter by weight range
    if min_weight is not None:
        query = query.filter(Basket.tare_weight >= min_weight)
    
    if max_weight is not None:
        query = query.filter(Basket.tare_weight <= max_weight)

    # Sort by newest first
    return query.order_by(desc(Basket.basket_id)).offset(skip).limit(limit).all()

# ============================
# CREATE
# ============================

def create_basket(db: Session, basket_in: BasketCreate):
    # 1. Check for duplicate basket code
    existing_basket = get_basket_by_code(db, basket_in.basket_code)
    if existing_basket:
        raise HTTPException(
            status_code=409,
            detail=f"Basket code '{basket_in.basket_code}' already exists."
        )

    # 2. Create object from schema
    db_basket = Basket(**basket_in.model_dump())
    
    # 3. Save to DB
    db.add(db_basket)
    db.commit()
    db.refresh(db_basket)
    
    return db_basket

# ============================
# UPDATE
# ============================

def update_basket(db: Session, basket_id: int, basket_in: BasketUpdate):
    # 1. Find the basket to update
    db_basket = get_basket_by_id(db, basket_id)
    if not db_basket:
        raise HTTPException(status_code=404, detail="Basket not found")

    # 2. Validate unique code if user is changing the basket_code
    if basket_in.basket_code and basket_in.basket_code != db_basket.basket_code:
        duplicate_check = get_basket_by_code(db, basket_in.basket_code)
        if duplicate_check:
            raise HTTPException(
                status_code=409, 
                detail=f"New basket code '{basket_in.basket_code}' already exists."
            )

    # 3. Update data
    # exclude_unset=True: Only update fields provided by the client
    update_data = basket_in.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(db_basket, field, value)

    db.commit()
    db.refresh(db_basket)
    return db_basket

# ============================
# DELETE
# ============================

def delete_basket(db: Session, basket_id: int):
    # 1. Find the basket
    db_basket = get_basket_by_id(db, basket_id)
    if not db_basket:
        raise HTTPException(status_code=404, detail="Basket not found")

    # 2. Safety check: Prevent deleting baskets currently in use
    if db_basket.status == BasketStatus.IN_USE:
        raise HTTPException(
            status_code=400, 
            detail="Cannot delete basket while it is IN_USE. Please empty the basket first."
        )

    # 3. Delete
    db.delete(db_basket)
    db.commit()
    return {"message": "Basket deleted successfully"}

# ============================
# EXCEL IMPORT
# ============================
def import_basket_from_excel(db: Session, file: UploadFile):
    try:
        df = pd.read_excel(file.file, header=0)
        df.columns = df.columns.str.strip()
        df = df.where(pd.notnull(df), None)
    except Exception as e:
        return {"status": False, "message": f"Lỗi đọc file Excel: {str(e)}"}

    success_count = 0
    error_rows = []

    def safe_str(val):
        if pd.isnull(val) or val is None or str(val).strip() in ['', 'nan', 'None']: return ""
        return str(val).strip()

    def safe_float(val):
        try: return float(val) if val is not None else 0.0
        except: return 0.0

    # Cache lại mã rổ để check trùng lặp (tránh gọi DB liên tục)
    existing_baskets = {b[0] for b in db.query(Basket.basket_code).all()}
    processed_codes_in_file = set()

    for index, row in df.iterrows():
        excel_row = index + 2
        
        # Ánh xạ theo tên cột trong file mẫu của bạn
        basket_code = safe_str(row.get('Mã rổ'))
        
        if not basket_code:
            continue

        # Check trùng lặp
        if basket_code in existing_baskets or basket_code in processed_codes_in_file:
            error_rows.append(f"Dòng {excel_row}: Mã rổ '{basket_code}' đã tồn tại hoặc bị trùng lặp.")
            continue

        tare_weight = safe_float(row.get('Trọng lượng'))
        
        if tare_weight <= 0:
            error_rows.append(f"Dòng {excel_row}: Rổ '{basket_code}' có trọng lượng <= 0.")
            continue

        try:
            new_basket = Basket(
                basket_code=basket_code,
                tare_weight=tare_weight,
                status=BasketStatus.READY, # Mặc định READY
                note="Nhập từ Excel"
            )
            db.add(new_basket)
            
            processed_codes_in_file.add(basket_code)
            success_count += 1
            
        except Exception as e:
            error_rows.append(f"Dòng {excel_row}: Lỗi dữ liệu ({str(e)})")

    try:
        db.commit()
    except Exception as e:
         db.rollback()
         return {"status": False, "message": f"Lỗi lưu Database: {str(e)}"}
    
    return {
        "status": True, 
        "success_count": success_count, 
        "errors": error_rows
    }