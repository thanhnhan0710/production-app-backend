import pandas as pd
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, or_
from fastapi import HTTPException, UploadFile
from typing import Optional, List

from app.models.standard import Standard
from app.models.product import Product
from app.models.dye_color import DyeColor
from app.schemas.standard_schema import StandardCreate, StandardUpdate

# ============================
# READ (Get Data)
# ============================

def get_standard_by_id(db: Session, standard_id: int):
    return (
        db.query(Standard)
        .options(joinedload(Standard.product), joinedload(Standard.dye_color)) # Load quan hệ
        .filter(Standard.standard_id == standard_id)
        .first()
    )

def get_standards(db: Session, skip: int = 0, limit: int = 100):
    return (
        db.query(Standard)
        .options(joinedload(Standard.product), joinedload(Standard.dye_color)) # Load quan hệ
        .order_by(desc(Standard.standard_id))
        .offset(skip)
        .limit(limit)
        .all()
    )

# ============================
# SEARCH
# ============================

def search_standards(
    db: Session,
    keyword: Optional[str] = None, 
    product_id: Optional[int] = None,
    dye_color_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100
):
    query = db.query(Standard).options(joinedload(Standard.product), joinedload(Standard.dye_color))

    if keyword:
        search_term = f"%{keyword}%"
        # Tìm trong Note, Appearance hoặc Mã sản phẩm, Tên màu
        query = query.join(Product, isouter=True).join(DyeColor, isouter=True).filter(
            or_(
                Standard.note.ilike(search_term),
                Standard.appearance.ilike(search_term),
                # [FIX] Sửa Product.name -> Product.item_code
                Product.item_code.ilike(search_term), 
                DyeColor.color_name.ilike(search_term) 
            )
        )
    
    if product_id:
        query = query.filter(Standard.product_id == product_id)
        
    if dye_color_id:
        query = query.filter(Standard.dye_color_id == dye_color_id)

    return query.order_by(desc(Standard.standard_id)).offset(skip).limit(limit).all()

# ============================
# CREATE
# ============================

def create_standard(db: Session, standard_in: StandardCreate):
    try:
        db_standard = Standard(**standard_in.model_dump())
        
        db.add(db_standard)
        db.commit()
        db.refresh(db_standard)
        
        return db_standard
    except Exception as e:
        db.rollback()
        print(f"Error creating standard: {str(e)}") 
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# ============================
# UPDATE
# ============================

def update_standard(db: Session, standard_id: int, standard_in: StandardUpdate):
    db_standard = get_standard_by_id(db, standard_id)
    if not db_standard:
        return None

    update_data = standard_in.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(db_standard, field, value)

    try:
        db.commit()
        db.refresh(db_standard)
        return db_standard
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database update error: {str(e)}")

# ============================
# DELETE
# ============================

def delete_standard(db: Session, standard_id: int):
    db_standard = get_standard_by_id(db, standard_id)
    if not db_standard:
        return False

    try:
        db.delete(db_standard)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")

# ============================
# EXCEL IMPORT
# ============================
def import_standard_from_excel(db: Session, file: UploadFile):
    try:
        df = pd.read_excel(file.file, header=0) # File chuẩn có header ở dòng 1
        df.columns = df.columns.str.strip()
        df = df.where(pd.notnull(df), None)
    except Exception as e:
        return {"status": False, "message": f"Lỗi đọc file Excel: {str(e)}"}

    success_count = 0
    error_rows = []

    def safe_str(val):
        if pd.isnull(val) or val is None or str(val).strip() in ['', 'nan', 'None']: return ""
        return str(val).strip()

    # Create a set to track product IDs processed in THIS file 
    # to prevent duplicates if the Excel has the same item twice
    processed_product_ids = set()

    for index, row in df.iterrows():
        excel_row = index + 2
        
        item_code = safe_str(row.get('Mã sản phẩm'))
        if not item_code:
            continue

        # 1. Check Product exists
        product = db.query(Product).filter(Product.item_code == item_code).first()
        if not product:
            error_rows.append(f"Dòng {excel_row}: Sản phẩm '{item_code}' không tồn tại.")
            continue

        # 2. Check for duplicates within the current Excel file processing
        if product.product_id in processed_product_ids:
            error_rows.append(f"Dòng {excel_row}: Sản phẩm '{item_code}' bị lặp lại trong file Excel.")
            continue

        # 3. Check Unique Standard for Product in Database
        existing_std = db.query(Standard).filter(Standard.product_id == product.product_id).first()
        if existing_std:
            error_rows.append(f"Dòng {excel_row}: Sản phẩm '{item_code}' đã có Standard trong hệ thống.")
            continue

        color_id = None 
        width = safe_str(row.get('Chiều rộng (mm)'))
        thick = safe_str(row.get('Độ dày (mm)'))
        strength = safe_str(row.get('Lực căng đứt (≥daN)'))
        elongation = safe_str(row.get('Giãn dài'))
        density = safe_str(row.get('Mật độ sợi ngang'))
        weight = safe_str(row.get('Trọng lượng (±10%,g/m)'))
        note = safe_str(row.get('Ghi chú'))
        appearance = safe_str(row.get('Cong')) 

        try:
            new_std = Standard(
                product_id=product.product_id,
                dye_color_id=color_id,
                width_mm=width if width else "0",
                thickness_mm=thick if thick else "0",
                breaking_strength_dan=strength if strength else "0",
                elongation_at_load_percent=elongation if elongation else "0",
                weft_density=density if density else "0",
                weight_gm=weight if weight else "0",
                appearance=appearance,
                note=note,
                color_fastness_dry=None,
                color_fastness_wet=None,
                delta_e=None
            )
            db.add(new_std)
            # Mark this product_id as processed to catch duplicates in the file
            processed_product_ids.add(product.product_id) 
            success_count += 1
            
        except Exception as e:
            error_rows.append(f"Dòng {excel_row}: Lỗi dữ liệu ({str(e)})")

    # Commit only after looping through all rows
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