from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.api import deps
from app.schemas.supplier_schema import SupplierResponse, SupplierCreate, SupplierUpdate
from app.services import supplier_service

router = APIRouter()

@router.get("/", response_model=List[SupplierResponse])
def read_suppliers(skip: int = 0, limit: int = 100, db: Session = Depends(deps.get_db)):
    return supplier_service.get_suppliers(db, skip=skip, limit=limit)

@router.post("/", response_model=SupplierResponse)
def create_supplier(sup: SupplierCreate, db: Session = Depends(deps.get_db)):
    return supplier_service.create_supplier(db, sup)

@router.put("/{sup_id}", response_model=SupplierResponse)
def update_supplier(sup_id: int, sup: SupplierUpdate, db: Session = Depends(deps.get_db)):
    updated_sup = supplier_service.update_supplier(db, sup_id, sup)
    if not updated_sup:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return updated_sup

@router.delete("/{sup_id}")
def delete_supplier(sup_id: int, db: Session = Depends(deps.get_db)):
    success = supplier_service.delete_supplier(db, sup_id)
    if not success:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return {"message": "Deleted successfully"}

@router.get("/search", response_model=List[SupplierResponse])
def search_suppliers(
    keyword: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db)
):
    return supplier_service.search_suppliers(db, keyword, skip, limit)
