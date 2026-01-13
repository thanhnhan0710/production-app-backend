from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from sqlalchemy import or_

from app.models.supplier import Supplier
from app.schemas.supplier_schema import SupplierCreate, SupplierUpdate


# =========================
# GET LIST
# =========================
def get_suppliers(db: Session, skip: int = 0, limit: int = 100):
    return (
        db.query(Supplier)
        .offset(skip)
        .limit(limit)
        .all()
    )


# =========================
# CREATE
# =========================
def create_supplier(db: Session, supplier: SupplierCreate):
    try:
        # model_dump() là phương thức của Pydantic v2
        db_sup = Supplier(**supplier.model_dump())
        db.add(db_sup)
        db.commit()
        db.refresh(db_sup)
        return db_sup

    except IntegrityError as e:
        db.rollback()
        # Log lỗi thực tế ra console để debug nếu cần: print(e)
        raise HTTPException(
            status_code=409,
            detail="Could not create supplier. Possible duplicate data or constraint violation."
        )


# =========================
# UPDATE (PATCH STYLE)
# =========================
def update_supplier(db: Session, sup_id: int, sup_data: SupplierUpdate):
    db_sup = db.get(Supplier, sup_id)
    if not db_sup:
        return None

    # exclude_unset=True: Chỉ lấy những trường user thực sự gửi lên
    update_data = sup_data.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(db_sup, key, value)

    try:
        db.commit()
        db.refresh(db_sup)
        return db_sup
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Update failed due to data integrity violation."
        )


# =========================
# DELETE
# =========================
def delete_supplier(db: Session, sup_id: int):
    db_sup = db.get(Supplier, sup_id)
    if not db_sup:
        return False

    db.delete(db_sup)
    db.commit()
    return True


# =========================
# SEARCH
# =========================
def search_suppliers(
    db: Session,
    keyword: str,
    skip: int = 0,
    limit: int = 100
):
    query = db.query(Supplier)

    # Nếu keyword là số → tìm theo ID
    if keyword.isdigit():
        query = query.filter(
            Supplier.supplier_id == int(keyword)
        )
    else:
        # Tìm kiếm Text trong các trường quan trọng mới
        search_filter = or_(
            Supplier.supplier_name.ilike(f"%{keyword}%"),
            Supplier.short_name.ilike(f"%{keyword}%"),    # Tên viết tắt
            Supplier.contact_person.ilike(f"%{keyword}%"), # Người liên hệ
            Supplier.email.ilike(f"%{keyword}%"),
            Supplier.tax_code.ilike(f"%{keyword}%"),      # Mã số thuế
            Supplier.address.ilike(f"%{keyword}%")
        )
        query = query.filter(search_filter)

    return (
        query
        .offset(skip)
        .limit(limit)
        .all()
    )