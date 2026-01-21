from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from app.models.bom_detail import BOMDetail, BOMComponentType
from app.schemas.bom_detail_schema import BOMDetailCreate, BOMDetailUpdate

# =========================
# GET LIST (BY BOM ID)
# =========================
def get_details_by_bom_id(
    db: Session, 
    bom_id: int
):
    """Lấy toàn bộ chi tiết của 1 BOM (Không phân trang vì BOM thường ít dòng)"""
    return db.query(BOMDetail).filter(BOMDetail.bom_id == bom_id).all()

# =========================
# ADVANCED SEARCH
# =========================
def search_bom_details(
    db: Session,
    bom_id: int = None,
    material_id: int = None,
    component_type: BOMComponentType = None,
    keyword: str = None,
    skip: int = 0,
    limit: int = 100
):
    """
    Tìm kiếm chi tiết vật tư (Dùng để trace ngược: Vật tư này nằm trong BOM nào?)
    """
    query = db.query(BOMDetail)

    if bom_id:
        query = query.filter(BOMDetail.bom_id == bom_id)

    if material_id:
        query = query.filter(BOMDetail.material_id == material_id)
        
    if component_type:
        query = query.filter(BOMDetail.component_type == component_type)

    if keyword:
        # Tìm trong ghi chú
        query = query.filter(BOMDetail.note.ilike(f"%{keyword}%"))

    return query.offset(skip).limit(limit).all()

# =========================
# CREATE
# =========================
def create_bom_detail(db: Session, data: BOMDetailCreate):
    # Tính toán quantity_gross logic (Nếu cần thiết backend tính lại cho chắc)
    # Gross = Standard * (1 + Wastage/100)
    # Tuy nhiên, ở đây ta tin tưởng data từ FE gửi lên hoặc tính toán ở Schema
    
    bom_detail = BOMDetail(**data.model_dump())
    db.add(bom_detail)
    db.commit()
    db.refresh(bom_detail)
    return bom_detail

# =========================
# UPDATE
# =========================
def update_bom_detail(
    db: Session, 
    detail_id: int, 
    data: BOMDetailUpdate
):
    detail = db.get(BOMDetail, detail_id)
    if not detail:
        return None

    update_data = data.model_dump(exclude_unset=True)

    for k, v in update_data.items():
        setattr(detail, k, v)

    # Có thể thêm logic: Nếu update quantity_standard -> Tự động tính lại quantity_gross
    # if 'quantity_standard' in update_data or 'wastage_rate' in update_data:
    #     std = detail.quantity_standard
    #     wst = detail.wastage_rate
    #     detail.quantity_gross = std * (1 + wst / 100)

    db.commit()
    db.refresh(detail)
    return detail

# =========================
# DELETE
# =========================
def delete_bom_detail(db: Session, detail_id: int):
    detail = db.get(BOMDetail, detail_id)
    if not detail:
        return False

    db.delete(detail)
    db.commit()
    return True

# =========================
# BULK DELETE (Theo BOM)
# =========================
def delete_all_details_in_bom(db: Session, bom_id: int):
    """Xóa trắng chi tiết để import lại"""
    db.query(BOMDetail).filter(BOMDetail.bom_id == bom_id).delete()
    db.commit()
    return True