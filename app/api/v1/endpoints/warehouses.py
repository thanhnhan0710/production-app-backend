from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.api import deps
from app.schemas.warehouse_schema import WarehouseCreate, WarehouseUpdate, WarehouseResponse
from app.services.warehouse_service import WarehouseService

router = APIRouter()

@router.get("/", response_model=List[WarehouseResponse])
def read_warehouses(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = Query(None, description="Tìm theo tên kho hoặc vị trí"),
    db: Session = Depends(deps.get_db)
):
    service = WarehouseService(db)
    return service.get_multi(skip=skip, limit=limit, search=search)

@router.post("/", response_model=WarehouseResponse)
def create_warehouse(
    warehouse_in: WarehouseCreate, 
    db: Session = Depends(deps.get_db)
):
    service = WarehouseService(db)
    return service.create(obj_in=warehouse_in)

@router.put("/{warehouse_id}", response_model=WarehouseResponse)
def update_warehouse(
    warehouse_id: int, 
    warehouse_in: WarehouseUpdate, 
    db: Session = Depends(deps.get_db)
):
    service = WarehouseService(db)
    return service.update(warehouse_id=warehouse_id, obj_in=warehouse_in)

@router.delete("/{warehouse_id}")
def delete_warehouse(
    warehouse_id: int, 
    db: Session = Depends(deps.get_db)
):
    service = WarehouseService(db)
    return service.delete(warehouse_id=warehouse_id)