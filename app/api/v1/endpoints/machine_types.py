from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List

from app.api import deps
from app.schemas.machine_type_schema import MachineTypeResponse, MachineTypeCreate, MachineTypeUpdate
from app.services import machine_type_service
from app.core.websockets import ws_manager

router = APIRouter()

@router.get("/", response_model=List[MachineTypeResponse])
def get_types(skip: int = 0, limit: int = 100, db: Session = Depends(deps.get_db)):
    return machine_type_service.get_machine_types(db, skip, limit)

@router.get("/search", response_model=List[MachineTypeResponse])
def search_types(keyword: str, skip: int = 0, limit: int = 100, db: Session = Depends(deps.get_db)):
    return machine_type_service.search_machine_types(db, keyword, skip, limit)

@router.post("/", response_model=MachineTypeResponse)
def create_type(data: MachineTypeCreate, background_tasks: BackgroundTasks, db: Session = Depends(deps.get_db)):
    new_type = machine_type_service.create_machine_type(db, data)
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_MACHINE_TYPES")
    return new_type

@router.put("/{type_id}", response_model=MachineTypeResponse)
def update_type(type_id: int, data: MachineTypeUpdate, background_tasks: BackgroundTasks, db: Session = Depends(deps.get_db)):
    mt = machine_type_service.update_machine_type(db, type_id, data)
    if not mt: raise HTTPException(status_code=404, detail="Type not found")
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_MACHINE_TYPES")
    return mt

@router.delete("/{type_id}")
def delete_type(type_id: int, background_tasks: BackgroundTasks, db: Session = Depends(deps.get_db)):
    success = machine_type_service.delete_machine_type(db, type_id)
    if not success: raise HTTPException(status_code=404, detail="Type not found")
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_MACHINE_TYPES")
    return {"message": "Deleted successfully"}