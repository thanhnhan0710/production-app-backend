from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc

from app.models.bom_header import BOMHeader
from app.schemas.bom_header_schema import BOMHeaderCreate, BOMHeaderUpdate

# =========================
# HELPER: DEACTIVATE OTHERS
# =========================
def _deactivate_other_versions(db: Session, product_id: int, exclude_bom_id: int = None):
    """
    Hàm nội bộ: Khi set 1 BOM là Active, cần Deactive các version cũ của Product đó.
    """
    query = db.query(BOMHeader).filter(
        BOMHeader.product_id == product_id,
        BOMHeader.is_active == True
    )
    
    if exclude_bom_id:
        query = query.filter(BOMHeader.bom_id != exclude_bom_id)
        
    versions = query.all()
    for v in versions:
        v.is_active = False
    
    # Lưu ý: Không commit ở đây để đảm bảo transaction atomic ở hàm gọi
    db.flush() 

# =========================
# GET LIST (ALL)
# =========================
def get_bom_headers(
    db: Session, 
    skip: int = 0, 
    limit: int = 100
):
    return (
        db.query(BOMHeader)
        .order_by(desc(BOMHeader.created_at))
        .offset(skip)
        .limit(limit)
        .all()
    )

# =========================
# GET ONE
# =========================
def get_bom_header_by_id(db: Session, bom_id: int):
    return db.get(BOMHeader, bom_id)

# =========================
# ADVANCED SEARCH & FILTER
# =========================
def search_bom_headers(
    db: Session,
    keyword: str = None,
    product_id: int = None,
    is_active: bool = None,
    skip: int = 0,
    limit: int = 100
):
    """
    Tìm kiếm BOM theo:
    - Keyword: Mã BOM hoặc Tên BOM
    - Filter: Theo ID sản phẩm hoặc trạng thái Active
    """
    query = db.query(BOMHeader)

    # 1. Filter theo Product (Rất quan trọng khi xem chi tiết 1 SP)
    if product_id:
        query = query.filter(BOMHeader.product_id == product_id)

    # 2. Filter theo trạng thái
    if is_active is not None:
        query = query.filter(BOMHeader.is_active == is_active)

    # 3. Search Keyword (Mã hoặc Tên)
    if keyword:
        search_filter = or_(
            BOMHeader.bom_code.ilike(f"%{keyword}%"),
            BOMHeader.bom_name.ilike(f"%{keyword}%")
        )
        query = query.filter(search_filter)

    return (
        query.order_by(desc(BOMHeader.version)) # Ưu tiên version mới nhất
        .offset(skip)
        .limit(limit)
        .all()
    )

# =========================
# CREATE
# =========================
def create_bom_header(db: Session, data: BOMHeaderCreate):
    # Logic: Nếu BOM mới là Active, hãy tắt các BOM cũ của SP này
    if data.is_active:
        _deactivate_other_versions(db, data.product_id)

    bom = BOMHeader(**data.model_dump())
    db.add(bom)
    db.commit()
    db.refresh(bom)
    return bom

# =========================
# UPDATE
# =========================
def update_bom_header(
    db: Session, 
    bom_id: int, 
    data: BOMHeaderUpdate
):
    bom = db.get(BOMHeader, bom_id)
    if not bom:
        return None

    update_data = data.model_dump(exclude_unset=True)

    # Logic: Nếu update set Active = True, tắt các cái khác
    if update_data.get("is_active") is True:
        # Lấy product_id từ data update hoặc từ bom hiện tại
        pid = update_data.get("product_id", bom.product_id)
        _deactivate_other_versions(db, product_id=pid, exclude_bom_id=bom_id)

    for k, v in update_data.items():
        setattr(bom, k, v)

    db.commit()
    db.refresh(bom)
    return bom

# =========================
# DELETE
# =========================
def delete_bom_header(db: Session, bom_id: int):
    bom = db.get(BOMHeader, bom_id)
    if not bom:
        return False

    db.delete(bom)
    db.commit()
    return True