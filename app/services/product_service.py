from fastapi import UploadFile
import pandas as pd
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from io import BytesIO

from app.models.product import Product
from app.models.product_type import ProductType
from app.schemas.product_schema import ProductCreate, ProductUpdate

# =========================
# GET LIST (Có phân trang & lọc theo loại)
# =========================
def get_products(db: Session, skip: int = 0, limit: int = 100, product_type_id: int = None):
    # Dùng joinedload để tự động JOIN bảng ProductType (tránh N+1 query)
    query = db.query(Product).options(joinedload(Product.product_type))
    
    if product_type_id:
        query = query.filter(Product.product_type_id == product_type_id)
        
    return query.offset(skip).limit(limit).all()

# =========================
# SEARCH (Tìm theo mã SP, ghi chú, hoặc TÊN loại SP)
# =========================
def search_products(db: Session, keyword: str, skip: int = 0, limit: int = 100):
    return (
        db.query(Product).options(joinedload(Product.product_type))
        .outerjoin(ProductType)
        .filter(
            or_(
                Product.item_code.ilike(f"%{keyword}%"),
                Product.note.ilike(f"%{keyword}%"),
                ProductType.type_name.ilike(f"%{keyword}%") # Tìm kiếm bằng tên loại
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
# UPDATE
# =========================
def update_product(db: Session, product_id: int, data: ProductUpdate):
    product = db.get(Product, product_id)
    if not product:
        return None
        
    for k, v in data.model_dump(exclude_unset=True).items():
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
# EXCEL IMPORT (Tự động map khóa ngoại)
# =========================
def import_products_from_excel(db: Session, file: UploadFile):
    try:
        df = pd.read_excel(file.file, header=1)
        df.columns = df.columns.str.strip()
        df = df.where(pd.notnull(df), None)
    except Exception as e:
        return {"status": False, "message": f"Lỗi đọc file Excel: {str(e)}"}

    success_count = 0
    error_rows = []

    # Cache danh sách Mã Sản Phẩm hiện có để kiểm tra trùng lặp nhanh
    existing_products = db.query(Product.item_code).all()
    existing_codes_set = {str(p[0]).strip().lower() for p in existing_products if p[0]}
    codes_in_current_excel = set()

    # Cache danh sách Loại Sản Phẩm để lấy ID (Key là tên loại viết thường)
    existing_types = db.query(ProductType).all()
    type_map = {t.type_name.strip().lower(): t.product_type_id for t in existing_types if t.type_name}

    for index, row in df.iterrows():
        excel_row_num = index + 3

        item_code_val = row.get('Item Code')
        if pd.isnull(item_code_val) or str(item_code_val).strip() in ['', 'nan', 'None']:
            continue 
            
        item_code = str(item_code_val).strip()
        item_code_lower = item_code.lower()

        # Kiểm tra trùng lặp trong DB và trong chính file Excel đang import
        if item_code_lower in existing_codes_set or item_code_lower in codes_in_current_excel:
            error_rows.append(f"Dòng {excel_row_num}: Mã sản phẩm '{item_code}' đã tồn tại.")
            continue

        codes_in_current_excel.add(item_code_lower)

        # Xử lý Khóa Ngoại: Loại Sản Phẩm
        type_val = row.get('Product Type') if 'Product Type' in df.columns else row.get('Loại sản phẩm')
        product_type_id = None
        
        if type_val and str(type_val).strip() not in ['', 'nan', 'None']:
            type_name = str(type_val).strip()
            type_key = type_name.lower()
            
            # Nếu tên Loại chưa có trong DB -> Tự động sinh loại mới
            if type_key not in type_map:
                new_pt = ProductType(type_name=type_name)
                db.add(new_pt)
                db.flush() # Lưu tạm vào session để lấy ID ngay lập tức
                type_map[type_key] = new_pt.product_type_id
            
            product_type_id = type_map[type_key]

        note_val = row.get('Note')
        note = str(note_val).strip() if not pd.isnull(note_val) and str(note_val).strip() not in ['', 'nan', 'None'] else None

        try:
            new_product = Product(
                item_code=item_code,
                product_type_id=product_type_id,
                note=note,
                image_url=None
            )
            db.add(new_product)
            success_count += 1
            
        except Exception as e:
            error_rows.append(f"Dòng {excel_row_num}: Lỗi dữ liệu ({str(e)})")

    # Lưu toàn bộ vào Database
    db.commit()
    
    return {
        "status": True, 
        "success_count": success_count, 
        "errors": error_rows
    }

# =========================
# EXCEL EXPORT
# =========================
def export_products_to_excel(db: Session):
    products = db.query(Product).options(joinedload(Product.product_type)).all()

    data = []
    for i, p in enumerate(products, 1):
        data.append({
            "No.": i,
            "Item Code": p.item_code,
            # Lấy tên loại sản phẩm qua relationship
            "Loại sản phẩm": p.product_type.type_name if p.product_type else "",
            "Note": p.note if p.note else ""
        })

    df = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Products')

    output.seek(0)
    return output