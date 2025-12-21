from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.api import deps
from app.schemas.yarn_schema import YarnResponse, YarnCreate, YarnUpdate
from app.services import yarn_service

router = APIRouter()

@router.get("/", response_model=List[YarnResponse])
def read_yarns(skip: int = 0, limit: int = 100, db: Session = Depends(deps.get_db)):
    return yarn_service.get_yarns(db, skip=skip, limit=limit)

@router.post("/", response_model=YarnResponse)
def create_yarn(yarn: YarnCreate, db: Session = Depends(deps.get_db)):
    return yarn_service.create_yarn(db, yarn)

@router.put("/{yarn_id}", response_model=YarnResponse)
def update_yarn(yarn_id: int, yarn: YarnUpdate, db: Session = Depends(deps.get_db)):
    updated_emp = yarn_service.update_yarn(db, yarn_id, yarn)
    if not updated_emp:
        raise HTTPException(status_code=404, detail="Yarn not found")
    return updated_emp

@router.delete("/{yarn_id}")
def delete_yarn(yarn_id: int, db: Session = Depends(deps.get_db)):
    success = yarn_service.delete_yarn(db, yarn_id)
    if not success:
        raise HTTPException(status_code=404, detail="Yarn not found")
    return {"message": "Deleted successfully"}