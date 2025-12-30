from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.api import deps
from app.schemas.material_schema import (
    MaterialResponse,
    MaterialCreate,
    MaterialUpdate
)
from app.services import material_service

router = APIRouter()

@router.get("/", response_model=List[MaterialResponse])
def read_materials(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db)
):
    return material_service.get_materials(db, skip=skip, limit=limit)
@router.get("/search", response_model=List[MaterialResponse])
def search_materials(
    keyword: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db)
):
    return material_service.search_materials(db, keyword, skip, limit)

@router.get("/{material_id}", response_model=MaterialResponse)
def read_material(
    material_id: int,
    db: Session = Depends(deps.get_db)
):
    material = material_service.get_material(db, material_id)
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    return material

@router.post("/", response_model=MaterialResponse)
def create_material(
    material: MaterialCreate,
    db: Session = Depends(deps.get_db)
):
    return material_service.create_material(db, material)

@router.put("/{material_id}", response_model=MaterialResponse)
def update_material(
    material_id: int,
    material: MaterialUpdate,
    db: Session = Depends(deps.get_db)
):
    updated_material = material_service.update_material(
        db, material_id, material
    )
    if not updated_material:
        raise HTTPException(status_code=404, detail="Material not found")
    return updated_material

@router.delete("/{material_id}")
def delete_material(
    material_id: int,
    db: Session = Depends(deps.get_db)
):
    success = material_service.delete_material(db, material_id)
    if not success:
        raise HTTPException(status_code=404, detail="Material not found")
    return {"message": "Deleted successfully"}


