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
        db_sup = Supplier(**supplier.model_dump())
        db.add(db_sup)
        db.commit()
        db.refresh(db_sup)
        return db_sup

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Supplier with this email already exists."
        )


# =========================
# UPDATE (PATCH STYLE)
# =========================
def update_supplier(db: Session, sup_id: int, sup_data: SupplierUpdate):
    db_sup = db.get(Supplier, sup_id)
    if not db_sup:
        return None

    update_data = sup_data.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(db_sup, key, value)

    db.commit()
    db.refresh(db_sup)
    return db_sup


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
        query = query.filter(
            or_(
                Supplier.supplier_name.ilike(f"%{keyword}%"),
                Supplier.email.ilike(f"%{keyword}%"),
                Supplier.phone.ilike(f"%{keyword}%"),
                Supplier.address.ilike(f"%{keyword}%"),
                Supplier.note.ilike(f"%{keyword}%")
            )
        )

    return (
        query
        .offset(skip)
        .limit(limit)
        .all()
    )
