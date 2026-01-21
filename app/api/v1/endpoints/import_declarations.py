from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from app.api import deps
from app.models.import_declaration import ImportType
from app.schemas.import_declaration_schema import (
    ImportDeclarationResponse, 
    ImportDeclarationCreate, 
    ImportDeclarationUpdate, 
    ImportDetailCreate, 
    ImportDetailUpdate,
    ImportDetailResponse
)
from app.services.import_declaration_service import ImportDeclarationService

router = APIRouter()

@router.get("/", response_model=List[ImportDeclarationResponse])
def read_import_declarations(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    import_type: Optional[ImportType] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    db: Session = Depends(deps.get_db)
):
    service = ImportDeclarationService(db)
    return service.get_multi(
        skip=skip, limit=limit, search=search, 
        import_type=import_type, from_date=from_date, to_date=to_date
    )

@router.post("/", response_model=ImportDeclarationResponse)
def create_import_declaration(
    declaration_in: ImportDeclarationCreate,
    db: Session = Depends(deps.get_db)
):
    return ImportDeclarationService(db).create(obj_in=declaration_in)

@router.get("/{declaration_id}", response_model=ImportDeclarationResponse)
def read_import_declaration(
    declaration_id: int,
    db: Session = Depends(deps.get_db)
):
    service = ImportDeclarationService(db)
    decl = service.get(declaration_id)
    if not decl:
        raise HTTPException(status_code=404, detail="Not found")
    return decl

@router.put("/{declaration_id}", response_model=ImportDeclarationResponse)
def update_import_declaration(
    declaration_id: int,
    declaration_in: ImportDeclarationUpdate,
    db: Session = Depends(deps.get_db)
):
    service = ImportDeclarationService(db)
    decl = service.get(declaration_id)
    if not decl:
        raise HTTPException(status_code=404, detail="Not found")
    return service.update(db_obj=decl, obj_in=declaration_in)

@router.delete("/{declaration_id}")
def delete_import_declaration(
    declaration_id: int,
    db: Session = Depends(deps.get_db)
):
    service = ImportDeclarationService(db)
    service.delete(declaration_id)
    return {"message": "Deleted successfully"}

# --- CHI TIẾT ---
@router.post("/{declaration_id}/details", response_model=ImportDetailResponse)
def add_detail(
    declaration_id: int,
    detail_in: ImportDetailCreate,
    db: Session = Depends(deps.get_db)
):
    return ImportDeclarationService(db).add_detail(declaration_id, detail_in)

@router.put("/details/{detail_id}", response_model=ImportDetailResponse)
def update_detail(
    detail_id: int,
    detail_in: ImportDetailUpdate,
    db: Session = Depends(deps.get_db)
):
    return ImportDeclarationService(db).update_detail(detail_id, detail_in)

@router.delete("/details/{detail_id}")
def delete_detail(
    detail_id: int,
    db: Session = Depends(deps.get_db)
):
    ImportDeclarationService(db).delete_detail(detail_id)
    return {"message": "Detail deleted successfully"}