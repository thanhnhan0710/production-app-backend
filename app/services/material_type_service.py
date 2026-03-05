import pandas as pd
from io import BytesIO
from sqlalchemy.orm import Session
from fastapi import HTTPException
from typing import Optional

from app.models.material_type import MaterialType
from app.schemas.material_type_schema import MaterialTypeCreate, MaterialTypeUpdate

# ============================
# READ
# ============================
def get_type_by_id(db: Session, type_id: int):
    return db.query(MaterialType).filter(MaterialType.type_id == type_id).first()

def get_type_by_name(db: Session, type_name: str):
    return db.query(MaterialType).filter(MaterialType.type_name == type_name).first()

def get_types(db: Session, skip: int = 0, limit: int = 100, search: Optional[str] = None):
    query = db.query(MaterialType)
    if search:
        search_term = f"%{search}%"
        query = query.filter(MaterialType.type_name.ilike(search_term))
    return query.offset(skip).limit(limit).all()

def count_types(db: Session):
    return db.query(MaterialType).count()

# ============================
# CREATE
# ============================
def create_type(db: Session, type_in: MaterialTypeCreate):
    if get_type_by_name(db, type_in.type_name):
        raise HTTPException(status_code=409, detail="Tên Loại nguyên vật liệu đã tồn tại.")
        
    db_type = MaterialType(**type_in.model_dump())
    db.add(db_type)
    db.commit()
    db.refresh(db_type)
    return db_type

# ============================
# UPDATE
# ============================
def update_type(db: Session, type_id: int, type_in: MaterialTypeUpdate):
    db_type = get_type_by_id(db, type_id)
    if not db_type:
        raise HTTPException(status_code=404, detail="Không tìm thấy Loại nguyên vật liệu.")

    if type_in.type_name and type_in.type_name != db_type.type_name:
        if get_type_by_name(db, type_in.type_name):
            raise HTTPException(status_code=409, detail="Tên Loại nguyên vật liệu đã tồn tại.")

    update_data = type_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_type, field, value)

    db.commit()
    db.refresh(db_type)
    return db_type

# ============================
# DELETE
# ============================
def delete_type(db: Session, type_id: int):
    db_type = get_type_by_id(db, type_id)
    if not db_type:
        raise HTTPException(status_code=404, detail="Không tìm thấy Loại nguyên vật liệu.")
        
    # Ràng buộc: Không cho xóa nếu đang có NVL thuộc loại này
    if db_type.materials:
        raise HTTPException(
            status_code=400, 
            detail="Không thể xóa! Đang có Nguyên vật liệu thuộc loại này."
        )

    db.delete(db_type)
    db.commit()
    return {"message": "Đã xóa Loại nguyên vật liệu thành công."}

# ============================
# EXPORT EXCEL
# ============================
def export_types_to_excel(db: Session):
    types = db.query(MaterialType).all()

    data = []
    for t in types:
        data.append({
            "No.": t.type_id,
            "Tên loại nguyên vật liệu": t.type_name,
            "Mô tả": t.description if t.description else ""
        })

    df = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Material_Types')

    output.seek(0)
    return output