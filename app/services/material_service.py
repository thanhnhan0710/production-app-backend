from fastapi import UploadFile
import pandas as pd
from pandas import io
from sqlalchemy.orm import Session
from sqlalchemy import or_
from fastapi import UploadFile
# Import Model và Schema tương ứng
from app.models.material import Material
from app.models.unit import Unit
from app.schemas.material_schema import MaterialCreate, MaterialUpdate
from io import BytesIO

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
                Material.material_name.ilike(search_term),
                Material.material_type.ilike(search_term),  # Tìm theo loại (Polyester...)
                Material.dtex.ilike(search_term),    # Tìm theo thông số (1000D...)
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

# =========================
# EXCEL IMPORT
# =========================
def import_materials_from_excel(db: Session, file: UploadFile):
    try:
        # Đọc file Excel. 
        # header=1 nghĩa là lấy dòng thứ 2 (index 1) làm tiêu đề cột
        df = pd.read_excel(file.file, header=1)
        # Chuẩn hóa NaN thành None để nhét vào Database không bị lỗi
        df = df.where(pd.notnull(df), None)
    except Exception as e:
        return {"status": False, "message": f"Lỗi đọc file Excel: {str(e)}"}

    # Lấy danh sách Unit để map. 
    units = db.query(Unit).all()
    
    # [LƯU Ý]: Lỗi lúc nãy "has no attribute 'name'" nằm ở đây. 
    # Nếu model Unit của bạn dùng `unit_name` thay vì `name`, hãy giữ nguyên dòng dưới đây.
    # Nếu bạn dùng trường khác (ví dụ: `code`), hãy thay chữ `u.unit_name` thành trường đó.
    unit_map = {getattr(u, 'unit_name', '').strip().lower(): getattr(u, 'unit_id', getattr(u, 'id', None)) for u in units}

    success_count = 0
    error_rows = []

    for index, row in df.iterrows():
        # Do Excel mất 2 dòng đầu (Title + Header), data bắt đầu từ dòng 3 (index pandas + 3)
        excel_row_num = index + 3 

        # Mã sợi lấy từ SHORT ITEM NAME
        material_name = str(row.get('SHORT ITEM NAME', '')).strip()
        if not material_name or material_name == 'None':
            continue  # Bỏ qua các dòng trống

        # 1. Kiểm tra trùng lặp
        if get_material_by_code(db, material_name):
            error_rows.append(f"Dòng {excel_row_num}: Mã '{material_name}' đã tồn tại.")
            continue

        # 2. Xử lý Map ID cho Đơn vị tính (Lấy từ cột BUY UNIT)
        buy_unit_str = str(row.get('BUY UNIT', '')).strip().lower()
        unit_id = unit_map.get(buy_unit_str)

        if not unit_id:
            error_rows.append(f"Dòng {excel_row_num}: Không tìm thấy đơn vị '{row.get('BUY UNIT')}' trong hệ thống.")
            continue

        # 3. Tạo data và insert
        try:
            # Ép kiểu an toàn cho Dtex (int)
            dtex_val = row.get('Dtex')
            dtex = int(float(dtex_val)) if pd.notnull(dtex_val) and str(dtex_val).strip() != '' else None

            # Ép kiểu an toàn cho Tồn kho (float)
            min_stock_val = row.get('MIN STOCK')
            min_stock = float(min_stock_val) if pd.notnull(min_stock_val) else 0.0

            # Ép kiểu an toàn cho kg/Bb (float)
            kg_bb_val = row.get('kg/Bb')
            kg_bb = float(kg_bb_val) if pd.notnull(kg_bb_val) and str(kg_bb_val).strip() != '' else None

            new_material = Material(
                material_name=material_name,
                material_code=str(row.get('FULL ITEM NAME', '')).strip() or None,
                material_type=str(row.get('YARN TYPE', '')).strip() or None,
                color=str(row.get('COLOR', '')).strip() or None,
                dtex=dtex,
                min_stock_level=min_stock,
                
                # Do file Excel không có Đơn vị sản xuất, dùng chung ID của BUY UNIT
                uom_base_id=unit_id,
                uom_production_id=unit_id, 
                
                kg_per_bobbin=kg_bb
            )
            db.add(new_material)
            success_count += 1
        except Exception as e:
            error_rows.append(f"Dòng {excel_row_num}: Lỗi dữ liệu ({str(e)})")

    db.commit()
    
    return {
        "status": True, 
        "success_count": success_count, 
        "errors": error_rows
    }

# =========================
# EXCEL EXPORT
# =========================
def export_materials_to_excel(db: Session):
    """
    Xuất danh sách vật tư ra file Excel dạng bytes
    """
    materials = db.query(Material).all()

    # Chuẩn bị dữ liệu map với các cột giống file Import ban đầu của bạn
    data = []
    for m in materials:
        # Lấy tên đơn vị (nếu có). Lưu ý: thay 'unit_name' bằng đúng tên cột trong bảng Unit của bạn
        buy_unit = getattr(m.uom_base, 'unit_name', '') if m.uom_base else ''

        data.append({
            "FULL ITEM NAME": m.material_code,
            "SHORT ITEM NAME": m.material_name,
            "YARN TYPE": m.material_type,
            "COLOR": m.color,
            "Dtex": m.dtex,
            "MIN STOCK": m.min_stock_level,
            "BUY UNIT": buy_unit,
            "kg/Bb": m.kg_per_bobbin
        })

    # Chuyển thành DataFrame
    df = pd.DataFrame(data)

    # Ghi ra bộ nhớ đệm (BytesIO) thay vì lưu thành file cứng trên server
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Materials')

    # Trỏ con trỏ về đầu stream để đọc
    output.seek(0)
    return output