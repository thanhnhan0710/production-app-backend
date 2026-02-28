from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List

from app.api import deps
from app.schemas.product_type_schema import ProductTypeResponse, ProductTypeCreate, ProductTypeUpdate
from app.services import product_type_service
from app.core.websockets import ws_manager

router = APIRouter()

@router.get("/", response_model=List[ProductTypeResponse])
def get_types(skip: int = 0, limit: int = 100, db: Session = Depends(deps.get_db)):
    return product_type_service.get_product_types(db, skip, limit)

@router.get("/search", response_model=List[ProductTypeResponse])
def search_types(
    keyword: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db)
):
    return product_type_service.search_product_types(db, keyword, skip, limit)

@router.post("/", response_model=ProductTypeResponse)
def create_type(
    data: ProductTypeCreate, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db)
):
    new_type = product_type_service.create_product_type(db, data)
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_PRODUCT_TYPES")
    return new_type

@router.put("/{type_id}", response_model=ProductTypeResponse)
def update_type(
    type_id: int, 
    data: ProductTypeUpdate, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db)
):
    pt = product_type_service.update_product_type(db, type_id, data)
    if not pt:
        raise HTTPException(status_code=404, detail="Type not found")
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_PRODUCT_TYPES")
    return pt

@router.delete("/{type_id}")
def delete_type(
    type_id: int, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db)
):
    success = product_type_service.delete_product_type(db, type_id)
    if not success:
        raise HTTPException(status_code=404, detail="Type not found")
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_PRODUCT_TYPES")
    return {"message": "Deleted successfully"}