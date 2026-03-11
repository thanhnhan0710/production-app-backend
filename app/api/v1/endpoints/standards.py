from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional

from app.api import deps
from app.schemas.standard_schema import (
    StandardResponse,
    StandardCreate,
    StandardUpdate
)
from app.services import standard_service
from app.core.websockets import ws_manager # Import WebSocket Manager

router = APIRouter()

# =========================
# GET LIST
# =========================
@router.get("/", response_model=List[StandardResponse])
def read_standards(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db)
):
    """
    Get list of standards (with pagination).
    """
    return standard_service.get_standards(db, skip, limit)


# =========================
# SEARCH (QUAN TRỌNG: Đặt trên GET ID)
# =========================
@router.get("/search", response_model=List[StandardResponse])
def search_standards(
    keyword: Optional[str] = None,
    product_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db)
):
    """
    Search standards by Keyword (Note, Curved, Product Item Code) 
    or Filters (Product ID).
    """
    return standard_service.search_standards(
        db=db,
        keyword=keyword,
        product_id=product_id,
        skip=skip,
        limit=limit
    )


# =========================
# GET DETAIL
# =========================
@router.get("/{standard_id}", response_model=StandardResponse)
def read_standard(
    standard_id: int,
    db: Session = Depends(deps.get_db)
):
    """
    Get specific standard details by ID.
    """
    standard = standard_service.get_standard_by_id(db, standard_id)
    if not standard:
        raise HTTPException(status_code=404, detail="Standard not found")
    return standard


# =========================
# CREATE (Có WebSocket)
# =========================
@router.post("/", response_model=StandardResponse)
def create_standard(
    standard_in: StandardCreate,
    background_tasks: BackgroundTasks, # Bổ sung BackgroundTasks
    db: Session = Depends(deps.get_db)
):
    """
    Create a new standard.
    """
    new_standard = standard_service.create_standard(db, standard_in)
    
    # Bắn tín hiệu WebSocket cho tất cả Client làm mới danh sách
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_STANDARDS")
    
    return new_standard


# =========================
# UPDATE (Có WebSocket)
# =========================
@router.put("/{standard_id}", response_model=StandardResponse)
def update_standard(
    standard_id: int,
    standard_in: StandardUpdate,
    background_tasks: BackgroundTasks, # Bổ sung BackgroundTasks
    db: Session = Depends(deps.get_db)
):
    """
    Update standard info.
    """
    updated_standard = standard_service.update_standard(db, standard_id, standard_in)
    if not updated_standard:
        raise HTTPException(status_code=404, detail="Standard not found")
    
    # Bắn tín hiệu WebSocket
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_STANDARDS")
    
    return updated_standard


# =========================
# DELETE (Có WebSocket)
# =========================
@router.delete("/{standard_id}")
def delete_standard(
    standard_id: int,
    background_tasks: BackgroundTasks, # Bổ sung BackgroundTasks
    db: Session = Depends(deps.get_db)
):
    """
    Delete a standard.
    """
    success = standard_service.delete_standard(db, standard_id)
    if not success:
         raise HTTPException(status_code=404, detail="Standard not found")
         
    # Bắn tín hiệu WebSocket
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_STANDARDS")
    
    return {"message": "Deleted successfully"}


# =========================
# IMPORT EXCEL (Có WebSocket)
# =========================
@router.post("/import", status_code=200)
def import_standard_excel(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(deps.get_db)
):
    """
    Import standards from Excel file.
    """
    if not file.filename.endswith(('.xls', '.xlsx')):
        raise HTTPException(status_code=400, detail="Chỉ chấp nhận file .xls hoặc .xlsx")
        
    result = standard_service.import_standard_from_excel(db, file)
    
    if result.get("status"):
        if result.get("success_count", 0) > 0:
            # Bắn tín hiệu WebSocket
            background_tasks.add_task(ws_manager.broadcast, "REFRESH_STANDARDS")
        return result
    else:
        raise HTTPException(status_code=400, detail=result.get("message"))