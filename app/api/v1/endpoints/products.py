from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.api import deps
from app.schemas.product_schema import (
    ProductResponse,
    ProductCreate,
    ProductUpdate
)
from app.services import product_service

router = APIRouter()


# =========================
# GET LIST
# =========================
@router.get("/", response_model=List[ProductResponse])
def read_products(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db)
):
    return product_service.get_products(db, skip, limit)


# =========================
# CREATE
# =========================
@router.post("/", response_model=ProductResponse)
def create_product(
    product: ProductCreate,
    db: Session = Depends(deps.get_db)
):
    return product_service.create_product(db, product)


# =========================
# UPDATE
# =========================
@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    product: ProductUpdate,
    db: Session = Depends(deps.get_db)
):
    updated_product = product_service.update_product(
        db, product_id, product
    )
    if not updated_product:
        raise HTTPException(status_code=404, detail="Product not found")
    return updated_product


# =========================
# DELETE
# =========================
@router.delete("/{product_id}")
def delete_product(
    product_id: int,
    db: Session = Depends(deps.get_db)
):
    success = product_service.delete_product(db, product_id)
    if not success:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"message": "Deleted successfully"}


# =========================
# SEARCH
# =========================
@router.get("/search", response_model=List[ProductResponse])
def search_products(
    keyword: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db)
):
    return product_service.search_products(
        db, keyword, skip, limit
    )
