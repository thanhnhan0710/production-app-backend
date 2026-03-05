from sqlalchemy.orm import Session
from sqlalchemy import or_
from fastapi import HTTPException
from typing import Optional

from app.models.supplier_category import SupplierCategory
from app.schemas.supplier_category_schema import SupplierCategoryCreate, SupplierCategoryUpdate

# ============================
# READ
# ============================

def get_category_by_id(db: Session, category_id: int):
    return db.query(SupplierCategory).filter(SupplierCategory.category_id == category_id).first()

def get_category_by_name(db: Session, category_name: str):
    return db.query(SupplierCategory).filter(SupplierCategory.category_name == category_name).first()

def get_categories(db: Session, skip: int = 0, limit: int = 100, search: Optional[str] = None):
    query = db.query(SupplierCategory)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(SupplierCategory.category_name.ilike(search_term))
        
    return query.offset(skip).limit(limit).all()

# ============================
# CREATE
# ============================

def create_category(db: Session, category_in: SupplierCategoryCreate):
    # Tránh trùng tên Loại
    if get_category_by_name(db, category_in.category_name):
        raise HTTPException(status_code=409, detail="Tên Loại nhà cung cấp đã tồn tại.")
        
    db_category = SupplierCategory(**category_in.model_dump())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

# ============================
# UPDATE
# ============================

def update_category(db: Session, category_id: int, category_in: SupplierCategoryUpdate):
    db_category = get_category_by_id(db, category_id)
    if not db_category:
        raise HTTPException(status_code=404, detail="Không tìm thấy Loại nhà cung cấp.")

    # Nếu cập nhật tên, check trùng lặp với record khác
    if category_in.category_name and category_in.category_name != db_category.category_name:
        if get_category_by_name(db, category_in.category_name):
            raise HTTPException(status_code=409, detail="Tên Loại nhà cung cấp đã tồn tại.")

    update_data = category_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_category, field, value)

    db.commit()
    db.refresh(db_category)
    return db_category

# ============================
# DELETE
# ============================

def delete_category(db: Session, category_id: int):
    db_category = get_category_by_id(db, category_id)
    if not db_category:
        raise HTTPException(status_code=404, detail="Không tìm thấy Loại nhà cung cấp.")
        
    # Check xem có Supplier nào đang tham chiếu đến Category này không
    if db_category.suppliers:
        raise HTTPException(
            status_code=400, 
            detail="Không thể xóa! Đang có Nhà cung cấp thuộc loại này."
        )

    db.delete(db_category)
    db.commit()
    return {"message": "Đã xóa Loại nhà cung cấp thành công."}