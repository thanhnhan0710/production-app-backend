from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.product import Product
from app.schemas.product_schema import ProductCreate, ProductUpdate


# =========================
# GET LIST
# =========================
def get_products(
    db: Session,
    skip: int = 0,
    limit: int = 100
):
    return (
        db.query(Product)
        .offset(skip)
        .limit(limit)
        .all()
    )


# =========================
# SEARCH (MÃ / TÊN / GHI CHÚ)
# =========================
def search_products(
    db: Session,
    keyword: str,
    skip: int = 0,
    limit: int = 100
):
    return (
        db.query(Product)
        .filter(
            or_(
                Product.item_code.ilike(f"%{keyword}%"),
                Product.note.ilike(f"%{keyword}%")
            )
        )
        .offset(skip)
        .limit(limit)
        .all()
    )


# =========================
# CREATE
# =========================
def create_product(db: Session, data: ProductCreate):
    product = Product(**data.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


# =========================
# UPDATE (PATCH STYLE)
# =========================
def update_product(
    db: Session,
    product_id: int,
    data: ProductUpdate
):
    product = db.get(Product, product_id)
    if not product:
        return None

    update_data = data.model_dump(exclude_unset=True)

    for k, v in update_data.items():
        setattr(product, k, v)

    db.commit()
    db.refresh(product)
    return product


# =========================
# DELETE
# =========================
def delete_product(db: Session, product_id: int):
    product = db.get(Product, product_id)
    if not product:
        return False

    db.delete(product)
    db.commit()
    return True
