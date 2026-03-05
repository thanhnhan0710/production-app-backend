from sqlalchemy.orm import Session
from sqlalchemy import or_
from fastapi import HTTPException
from typing import Optional

from app.models.supplier import Supplier
from app.models.supplier_category import SupplierCategory
from app.schemas.supplier_schema import SupplierCreate, SupplierUpdate

# ============================
# READ
# ============================

def get_supplier_by_id(db: Session, supplier_id: int):
    return db.query(Supplier).filter(Supplier.supplier_id == supplier_id).first()

def get_supplier_by_name(db: Session, supplier_name: str):
    return db.query(Supplier).filter(Supplier.supplier_name == supplier_name).first()

def get_suppliers(
    db: Session, 
    skip: int = 0, 
    limit: int = 100, 
    search: Optional[str] = None,
    category_id: Optional[int] = None,
    is_active: Optional[bool] = None
):
    query = db.query(Supplier)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Supplier.supplier_name.ilike(search_term),
                Supplier.short_name.ilike(search_term)
            )
        )
        
    if category_id is not None:
        query = query.filter(Supplier.category_id == category_id)
        
    if is_active is not None:
        query = query.filter(Supplier.is_active == is_active)
        
    return query.offset(skip).limit(limit).all()

# ============================
# CREATE
# ============================

def create_supplier(db: Session, supplier_in: SupplierCreate):
    # 1. Tránh trùng tên
    if get_supplier_by_name(db, supplier_in.supplier_name):
        raise HTTPException(status_code=409, detail="Tên Nhà cung cấp đã tồn tại.")
        
    # 2. Validate category_id (nếu có truyền lên)
    if supplier_in.category_id:
        category = db.query(SupplierCategory).filter(SupplierCategory.category_id == supplier_in.category_id).first()
        if not category:
            raise HTTPException(status_code=400, detail="Loại nhà cung cấp không hợp lệ.")

    # 3. Save
    db_supplier = Supplier(**supplier_in.model_dump())
    db.add(db_supplier)
    db.commit()
    db.refresh(db_supplier)
    return db_supplier

# ============================
# UPDATE
# ============================

def update_supplier(db: Session, supplier_id: int, supplier_in: SupplierUpdate):
    db_supplier = get_supplier_by_id(db, supplier_id)
    if not db_supplier:
        raise HTTPException(status_code=404, detail="Không tìm thấy Nhà cung cấp.")

    # Validate duplicate name
    if supplier_in.supplier_name and supplier_in.supplier_name != db_supplier.supplier_name:
        if get_supplier_by_name(db, supplier_in.supplier_name):
            raise HTTPException(status_code=409, detail="Tên Nhà cung cấp đã tồn tại.")
            
    # Validate category
    if supplier_in.category_id and supplier_in.category_id != db_supplier.category_id:
        category = db.query(SupplierCategory).filter(SupplierCategory.category_id == supplier_in.category_id).first()
        if not category:
            raise HTTPException(status_code=400, detail="Loại nhà cung cấp không hợp lệ.")

    update_data = supplier_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_supplier, field, value)

    db.commit()
    db.refresh(db_supplier)
    return db_supplier

# ============================
# DELETE
# ============================

def delete_supplier(db: Session, supplier_id: int):
    db_supplier = get_supplier_by_id(db, supplier_id)
    if not db_supplier:
        raise HTTPException(status_code=404, detail="Không tìm thấy Nhà cung cấp.")

    # Thường thì với ERP ta không xóa cứng (Hard Delete) mà sẽ ẩn đi (Soft Delete)
    # Bằng cách cập nhật is_active = False. Nhưng nếu bạn muốn xóa cứng:
    db.delete(db_supplier)
    db.commit()
    return {"message": "Đã xóa Nhà cung cấp thành công."}