from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List

from app.api import deps
from app.schemas.machine_status_schema import MachineStatusResponse, MachineStatusCreate, MachineStatusUpdate
from app.services import machine_status_service
from app.core.websockets import ws_manager

router = APIRouter()

@router.get("/", response_model=List[MachineStatusResponse])
def get_statuses(skip: int = 0, limit: int = 100, db: Session = Depends(deps.get_db)):
    return machine_status_service.get_machine_statuses(db, skip, limit)

@router.get("/search", response_model=List[MachineStatusResponse])
def search_statuses(keyword: str, skip: int = 0, limit: int = 100, db: Session = Depends(deps.get_db)):
    return machine_status_service.search_machine_statuses(db, keyword, skip, limit)

@router.post("/", response_model=MachineStatusResponse)
def create_status(data: MachineStatusCreate, background_tasks: BackgroundTasks, db: Session = Depends(deps.get_db)):
    new_status = machine_status_service.create_machine_status(db, data)
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_MACHINE_STATUSES")
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_MACHINES") # Reset máy nếu cần
    return new_status

@router.put("/{status_id}", response_model=MachineStatusResponse)
def update_status(status_id: int, data: MachineStatusUpdate, background_tasks: BackgroundTasks, db: Session = Depends(deps.get_db)):
    ms = machine_status_service.update_machine_status(db, status_id, data)
    if not ms: raise HTTPException(status_code=404, detail="Status not found")
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_MACHINE_STATUSES")
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_MACHINES")
    return ms

@router.delete("/{status_id}")
def delete_status(status_id: int, background_tasks: BackgroundTasks, db: Session = Depends(deps.get_db)):
    success = machine_status_service.delete_machine_status(db, status_id)
    if not success: raise HTTPException(status_code=404, detail="Status not found")
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_MACHINE_STATUSES")
    return {"message": "Deleted successfully"}