from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List

from app.api import deps
from app.schemas.area_schema import AreaResponse, AreaCreate, AreaUpdate
from app.services import area_service
from app.core.websockets import ws_manager

router = APIRouter()

@router.get("/", response_model=List[AreaResponse])
def get_areas(skip: int = 0, limit: int = 100, db: Session = Depends(deps.get_db)):
    return area_service.get_areas(db, skip, limit)

@router.get("/search", response_model=List[AreaResponse])
def search_areas(keyword: str, skip: int = 0, limit: int = 100, db: Session = Depends(deps.get_db)):
    return area_service.search_areas(db, keyword, skip, limit)

@router.post("/", response_model=AreaResponse)
def create_area(data: AreaCreate, background_tasks: BackgroundTasks, db: Session = Depends(deps.get_db)):
    new_area = area_service.create_area(db, data)
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_AREAS")
    return new_area

@router.put("/{area_id}", response_model=AreaResponse)
def update_area(area_id: int, data: AreaUpdate, background_tasks: BackgroundTasks, db: Session = Depends(deps.get_db)):
    area = area_service.update_area(db, area_id, data)
    if not area: raise HTTPException(status_code=404, detail="Area not found")
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_AREAS")
    # Bắn tín hiệu làm mới máy móc nếu cần thiết
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_MACHINES")
    return area

@router.delete("/{area_id}")
def delete_area(area_id: int, background_tasks: BackgroundTasks, db: Session = Depends(deps.get_db)):
    success = area_service.delete_area(db, area_id)
    if not success: raise HTTPException(status_code=404, detail="Area not found")
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_AREAS")
    return {"message": "Deleted successfully"}