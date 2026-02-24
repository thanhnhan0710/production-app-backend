from fastapi import UploadFile
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import or_
from io import BytesIO
from app.models.product import Product
from app.schemas.product_schema import ProductCreate, ProductUpdate


# =========================
# GET LIST
# =========================
def get_products(
    db: Session,
    skip: int = 0,
    limit: int = 100
):
    return (
        db.query(Product)
        .offset(skip)
        .limit(limit)
        .all()
    )


# =========================
# SEARCH (MÃ / TÊN / GHI CHÚ)
# =========================
def search_products(
    db: Session,
    keyword: str,
    skip: int = 0,
    limit: int = 100
):
    return (
        db.query(Product)
        .filter(
            or_(
                Product.item_code.ilike(f"%{keyword}%"),
                Product.note.ilike(f"%{keyword}%")
            )
        )
        .offset(skip)
        .limit(limit)
        .all()
    )


# =========================
# CREATE
# =========================
def create_product(db: Session, data: ProductCreate):
    product = Product(**data.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


# =========================
# UPDATE (PATCH STYLE)
# =========================
def update_product(
    db: Session,
    product_id: int,
    data: ProductUpdate
):
    product = db.get(Product, product_id)
    if not product:
        return None

    update_data = data.model_dump(exclude_unset=True)

    for k, v in update_data.items():
        setattr(product, k, v)

    db.commit()
    db.refresh(product)
    return product


# =========================
# DELETE
# =========================
def delete_product(db: Session, product_id: int):
    product = db.get(Product, product_id)
    if not product:
        return False

    db.delete(product)
    db.commit()
    return True

# =========================
# GET BY CODE (Hỗ trợ check trùng lặp)
# =========================
def get_product_by_code(db: Session, item_code: str):
    return db.query(Product).filter(Product.item_code == item_code).first()

# =========================
# EXCEL IMPORT (Đã sửa lỗi trùng lặp)
# =========================
def import_products_from_excel(db: Session, file: UploadFile):
    try:
        # header=1 vì dòng 1 là tiêu đề chung, dòng 2 mới là cột Header
        df = pd.read_excel(file.file, header=1)
        
        # Xóa khoảng trắng thừa ở tiêu đề cột
        df.columns = df.columns.str.strip()
        
        # Chuyển NaN thành None
        df = df.where(pd.notnull(df), None)
    except Exception as e:
        return {"status": False, "message": f"Lỗi đọc file Excel: {str(e)}"}

    success_count = 0
    error_rows = []

    # 1. Lấy tất cả item_code đang có trong DB bỏ vào một Set để check siêu nhanh
    existing_products = db.query(Product.item_code).all()
    # Chuyển thành set các chuỗi đã strip và viết thường (để so sánh không phân biệt hoa thường)
    existing_codes_set = {str(p[0]).strip().lower() for p in existing_products if p[0]}

    # Set để theo dõi các mã trùng lặp BÊN TRONG CHÍNH FILE EXCEL
    codes_in_current_excel = set()

    for index, row in df.iterrows():
        excel_row_num = index + 3 # Dòng thực tế trên file Excel

        # Trích xuất mã sản phẩm an toàn
        item_code_val = row.get('Item Code')
        if pd.isnull(item_code_val) or str(item_code_val).strip() in ['', 'nan', 'None']:
            continue # Bỏ qua dòng trống
            
        item_code = str(item_code_val).strip()
        item_code_lower = item_code.lower()

        # 2. Kiểm tra trùng lặp (Với DB cũ VÀ với các dòng trước đó trong chính file Excel)
        if item_code_lower in existing_codes_set or item_code_lower in codes_in_current_excel:
            error_rows.append(f"Dòng {excel_row_num}: Mã sản phẩm '{item_code}' đã tồn tại.")
            continue

        # Thêm mã này vào set theo dõi file Excel hiện tại
        codes_in_current_excel.add(item_code_lower)

        # 3. Xử lý ghi chú
        note_val = row.get('Note')
        note = str(note_val).strip() if not pd.isnull(note_val) and str(note_val).strip() not in ['', 'nan', 'None'] else None

        try:
            # 4. Tạo data và insert
            new_product = Product(
                item_code=item_code,
                note=note,
                image_url=None
            )
            db.add(new_product)
            success_count += 1
            
        except Exception as e:
            error_rows.append(f"Dòng {excel_row_num}: Lỗi dữ liệu ({str(e)})")

    # Commit toàn bộ thay đổi
    db.commit()
    
    return {
        "status": True, 
        "success_count": success_count, 
        "errors": error_rows
    }

# =========================
# EXCEL EXPORT (XUẤT FILE)
# =========================
def export_products_to_excel(db: Session):
    # Lấy toàn bộ sản phẩm
    products = db.query(Product).all()

    # Tạo data map với các cột: No., Item Code, Note
    data = []
    for i, p in enumerate(products, 1):
        data.append({
            "No.": i,
            "Item Code": p.item_code,
            "Note": p.note if p.note else ""
        })

    df = pd.DataFrame(data)
    
    # Ghi dữ liệu ra bộ nhớ ảo (RAM) thay vì lưu thành file vật lý
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Products')

    # Đưa con trỏ đọc về đầu file
    output.seek(0)
    return output