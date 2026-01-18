from sqlalchemy.orm import Session
from sqlalchemy import or_

# Import Model và Schema tương ứng
from app.models.material import Material
from app.schemas.material_schema import MaterialCreate, MaterialUpdate

# =========================
# GET LIST (Phân trang)
# =========================
def get_materials(
    db: Session,
    skip: int = 0,
    limit: int = 100
):
    """
    Lấy danh sách vật tư có phân trang.
    """
    return (
        db.query(Material)
        .order_by(Material.id.desc())  # Sắp xếp mới nhất lên đầu
        .offset(skip)
        .limit(limit)
        .all()
    )

# =========================
# GET ONE (Lấy chi tiết)
# =========================
def get_material_by_id(db: Session, material_id: int):
    """
    Lấy thông tin một vật tư theo ID.
    """
    return db.get(Material, material_id)

# =========================
# GET BY CODE (Check trùng)
# =========================
def get_material_by_code(db: Session, material_code: str):
    """
    Hàm tiện ích để kiểm tra mã code đã tồn tại chưa.
    """
    return db.query(Material).filter(Material.material_code == material_code).first()

# =========================
# SEARCH (Nâng cao)
# =========================
def search_materials(
    db: Session,
    keyword: str,
    skip: int = 0,
    limit: int = 100
):
    """
    Tìm kiếm vật tư theo từ khóa.
    Phạm vi tìm kiếm: Mã sợi, Tên sợi, Loại, Denier, HS Code.
    """
    search_term = f"%{keyword}%"
    
    return (
        db.query(Material)
        .filter(
            or_(
                Material.material_code.ilike(search_term),  # Tìm theo mã
                Material.material_name.ilike(search_term),  # Tìm theo tên
                Material.material_type.ilike(search_term),  # Tìm theo loại (Polyester...)
                Material.spec_denier.ilike(search_term),    # Tìm theo thông số (1000D...)
                Material.hs_code.ilike(search_term)         # Tìm theo HS Code
            )
        )
        .offset(skip)
        .limit(limit)
        .all()
    )

# =========================
# CREATE
# =========================
def create_material(db: Session, data: MaterialCreate):
    """
    Tạo mới vật tư.
    Lưu ý: Nên check trùng material_code ở lớp Router hoặc Service trước khi gọi hàm này
    để tránh lỗi IntegrityError nếu DB đã set unique.
    """
    # Chuyển đổi Pydantic model sang dict
    material_data = data.model_dump()
    
    # Tạo instance SQLAlchemy
    material = Material(**material_data)
    
    db.add(material)
    db.commit()
    db.refresh(material) # Lấy lại data từ DB (bao gồm ID tự sinh)
    return material

# =========================
# UPDATE (PATCH STYLE)
# =========================
def update_material(
    db: Session,
    material_id: int,
    data: MaterialUpdate
):
    """
    Cập nhật thông tin vật tư.
    Chỉ cập nhật các trường được gửi lên (exclude_unset=True).
    """
    material = db.get(Material, material_id)
    if not material:
        return None

    # Lấy dict các trường cần update, bỏ qua các trường None (không gửi lên)
    update_data = data.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(material, key, value)

    db.add(material) # Đảm bảo session track object này
    db.commit()
    db.refresh(material)
    return material

# =========================
# DELETE
# =========================
def delete_material(db: Session, material_id: int):
    """
    Xóa vật tư khỏi hệ thống.
    """
    material = db.get(Material, material_id)
    if not material:
        return False

    db.delete(material)
    db.commit()
    return True