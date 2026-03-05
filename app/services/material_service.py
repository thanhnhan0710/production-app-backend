from sqlalchemy.orm import Session
from sqlalchemy import or_
from fastapi import HTTPException
from typing import Optional

from app.models.material import Material
from app.models.material_type import MaterialType
from app.models.supplier import Supplier
from app.schemas.material_schema import MaterialCreate, MaterialUpdate
import pandas as pd
from io import BytesIO
from sqlalchemy.orm import joinedload

# ============================
# READ
# ============================
def get_material_by_id(db: Session, material_id: int):
    return db.query(Material).filter(Material.material_id == material_id).first()

def get_material_by_code(db: Session, material_code: str):
    return db.query(Material).filter(Material.material_code == material_code).first()

def get_materials(
    db: Session, 
    skip: int = 0, 
    limit: int = 100, 
    search: Optional[str] = None,
    type_id: Optional[int] = None,
    supplier_id: Optional[int] = None
):
    query = db.query(Material)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Material.material_code.ilike(search_term),
                Material.material_name.ilike(search_term)
            )
        )
        
    if type_id is not None:
        query = query.filter(Material.type_id == type_id)
        
    if supplier_id is not None:
        query = query.filter(Material.supplier_id == supplier_id)
        
    return query.offset(skip).limit(limit).all()

def count_materials(db: Session):
    return db.query(Material).count()

# ============================
# CREATE
# ============================
def create_material(db: Session, material_in: MaterialCreate):
    # 1. Tránh trùng mã NVL
    if get_material_by_code(db, material_in.material_code):
        raise HTTPException(status_code=409, detail="Mã Nguyên vật liệu đã tồn tại.")
        
    # 2. Validate Type & Supplier
    if material_in.type_id:
        if not db.query(MaterialType).filter(MaterialType.type_id == material_in.type_id).first():
            raise HTTPException(status_code=400, detail="Loại nguyên vật liệu không hợp lệ.")
            
    if material_in.supplier_id:
        if not db.query(Supplier).filter(Supplier.supplier_id == material_in.supplier_id).first():
            raise HTTPException(status_code=400, detail="Nhà cung cấp không hợp lệ.")

    # 3. Lưu
    db_material = Material(**material_in.model_dump())
    db.add(db_material)
    db.commit()
    db.refresh(db_material)
    return db_material

# ============================
# UPDATE
# ============================
def update_material(db: Session, material_id: int, material_in: MaterialUpdate):
    db_material = get_material_by_id(db, material_id)
    if not db_material:
        raise HTTPException(status_code=404, detail="Không tìm thấy Nguyên vật liệu.")

    # Validate Mã NVL
    if material_in.material_code and material_in.material_code != db_material.material_code:
        if get_material_by_code(db, material_in.material_code):
            raise HTTPException(status_code=409, detail="Mã Nguyên vật liệu đã tồn tại.")
            
    # Validate Khóa ngoại
    if material_in.type_id and material_in.type_id != db_material.type_id:
        if not db.query(MaterialType).filter(MaterialType.type_id == material_in.type_id).first():
            raise HTTPException(status_code=400, detail="Loại nguyên vật liệu không hợp lệ.")
            
    if material_in.supplier_id and material_in.supplier_id != db_material.supplier_id:
        if not db.query(Supplier).filter(Supplier.supplier_id == material_in.supplier_id).first():
            raise HTTPException(status_code=400, detail="Nhà cung cấp không hợp lệ.")

    update_data = material_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_material, field, value)

    db.commit()
    db.refresh(db_material)
    return db_material

# ============================
# DELETE
# ============================
def delete_material(db: Session, material_id: int):
    db_material = get_material_by_id(db, material_id)
    if not db_material:
        raise HTTPException(status_code=404, detail="Không tìm thấy Nguyên vật liệu.")

    db.delete(db_material)
    db.commit()
    return {"message": "Đã xóa Nguyên vật liệu thành công."}

# ============================
# EXPORT EXCEL
# ============================
def export_materials_to_excel(db: Session, type_id: Optional[int] = None, supplier_id: Optional[int] = None):
    # Dùng joinedload để lấy luôn tên Loại và tên NCC, tránh lỗi query N+1
    query = db.query(Material).options(
        joinedload(Material.material_type),
        joinedload(Material.supplier)
    )
    
    # Áp dụng bộ lọc nếu có truyền ID
    if type_id is not None:
        query = query.filter(Material.type_id == type_id)
    if supplier_id is not None:
        query = query.filter(Material.supplier_id == supplier_id)
        
    materials = query.all()

    data = []
    for i, m in enumerate(materials, 1):
        data.append({
            "STT": i,
            "Mã NVL": m.material_code,
            "Tên NVL": m.material_name,
            "Loại NVL": m.material_type.type_name if m.material_type else "",
            "Nhà cung cấp": m.supplier.supplier_name if m.supplier else "",
            "Màu sắc": m.color if m.color else "",
            "Dtex": m.dtex if m.dtex else "",
            "Filament": m.filament if m.filament else "",
            "Mức tồn kho Min": m.min_stock_level,
            "Kg/Cuộn": m.kg_per_bobbin if m.kg_per_bobbin else ""
        })

    df = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Materials')

    output.seek(0)
    return output