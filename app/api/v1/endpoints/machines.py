from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.api import deps
from app.schemas.machine_schema import (
    MachineResponse,
    MachineCreate,
    MachineUpdate
)
from app.services import machine_service

router = APIRouter()


# =========================
# GET LIST
# =========================
@router.get("/", response_model=List[MachineResponse])
def read_machines(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db)
):
    return machine_service.get_machines(db, skip=skip, limit=limit)


# =========================
# CREATE
# =========================
@router.post("/", response_model=MachineResponse)
def create_machine(
    machine: MachineCreate,
    db: Session = Depends(deps.get_db)
):
    return machine_service.create_machine(db, machine)


# =========================
# UPDATE
# =========================
@router.put("/{machine_id}", response_model=MachineResponse)
def update_machine(
    machine_id: int,
    machine: MachineUpdate,
    db: Session = Depends(deps.get_db)
):
    updated_machine = machine_service.update_machine(
        db, machine_id, machine
    )
    if not updated_machine:
        raise HTTPException(status_code=404, detail="Machine not found")
    return updated_machine


# =========================
# DELETE
# =========================
@router.delete("/{machine_id}")
def delete_machine(
    machine_id: int,
    db: Session = Depends(deps.get_db)
):
    success = machine_service.delete_machine(db, machine_id)
    if not success:
        raise HTTPException(status_code=404, detail="Machine not found")
    return {"message": "Deleted successfully"}


# =========================
# SEARCH
# =========================
@router.get("/search", response_model=List[MachineResponse])
def search_machines(
    keyword: str | None = None,
    status: str | None = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db)
):
    return machine_service.search_machines(
        db=db,
        keyword=keyword,
        status=status,
        skip=skip,
        limit=limit
    )
