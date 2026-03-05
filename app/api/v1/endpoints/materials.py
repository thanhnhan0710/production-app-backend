from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional

from app.api import deps
from app.core.websockets import ws_manager

from app.schemas.material_schema import MaterialCreate, MaterialUpdate, MaterialResponse
from app.services import material_service

router = APIRouter()

@router.get("/count", response_model=int)
def get_material_count(db: Session = Depends(deps.get_db)):
    """Lấy tổng số lượng Nguyên vật liệu"""
    return material_service.count_materials(db)

@router.get("/", response_model=List[MaterialResponse])
def read_materials(
    skip: int = 0, 
    limit: int = 100, 
    search: Optional[str] = None,
    type_id: Optional[int] = None,
    supplier_id: Optional[int] = None,
    db: Session = Depends(deps.get_db)
):
    """Lấy danh sách Nguyên vật liệu"""
    return material_service.get_materials(
        db, skip=skip, limit=limit, search=search, type_id=type_id, supplier_id=supplier_id
    )

@router.get("/{material_id}", response_model=MaterialResponse)
def read_material(material_id: int, db: Session = Depends(deps.get_db)):
    """Lấy chi tiết 1 Nguyên vật liệu"""
    material = material_service.get_material_by_id(db, material_id)
    if not material:
        raise HTTPException(status_code=404, detail="Không tìm thấy Nguyên vật liệu.")
    return material

@router.post("/", response_model=MaterialResponse)
def create_material(
    material_in: MaterialCreate, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db)
):
    """Thêm mới Nguyên vật liệu"""
    new_material = material_service.create_material(db, material_in)
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_MATERIALS")
    return new_material

@router.put("/{material_id}", response_model=MaterialResponse)
def update_material(
    material_id: int, 
    material_in: MaterialUpdate, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db)
):
    """Cập nhật Nguyên vật liệu"""
    updated_material = material_service.update_material(db, material_id, material_in)
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_MATERIALS")
    return updated_material

@router.delete("/{material_id}")
def delete_material(
    material_id: int, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db)
):
    """Xóa Nguyên vật liệu"""
    result = material_service.delete_material(db, material_id)
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_MATERIALS")
    return result

@router.get("/export/excel", status_code=200)
def export_excel(
    type_id: Optional[int] = None,
    supplier_id: Optional[int] = None,
    db: Session = Depends(deps.get_db)
):
    """Xuất danh sách Nguyên vật liệu ra file Excel (Hỗ trợ xuất tất cả hoặc lọc theo Loại và NCC)"""
    output = material_service.export_materials_to_excel(db, type_id=type_id, supplier_id=supplier_id)
    
    headers = {
        'Content-Disposition': 'attachment; filename="Danh_Muc_Nguyen_Vat_Lieu.xlsx"'
    }
    
    return StreamingResponse(
        output, 
        headers=headers, 
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )