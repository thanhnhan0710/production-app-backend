from sqlalchemy.orm import Session, joinedload
<<<<<<< HEAD
from sqlalchemy import or_, and_, desc
from datetime import date
from typing import Optional
from sqlalchemy import func, distinct, cast, Date

# Import Models
=======
from sqlalchemy import Date, cast, distinct, func, or_, and_, desc
from datetime import date
from typing import Optional

# Import Models
from app.models.weaving_basket_ticket import WeavingBasketTicket
>>>>>>> c468be65d7388abd40a800c84aa27cfe56d2c0d3
from app.models.weaving_daily_production import WeavingDailyProduction
from app.models.product import Product

# Import Schemas
from app.schemas.weaving_daily_production_schema import WeavingProductionCreate, WeavingProductionUpdate
<<<<<<< HEAD
from app.models.weaving_basket_ticket import WeavingBasketTicket
=======
>>>>>>> c468be65d7388abd40a800c84aa27cfe56d2c0d3

# =========================
# GET LIST (CƠ BẢN)
# =========================
def get_productions(
    db: Session,
    skip: int = 0,
    limit: int = 100
):
    """
    Lấy danh sách sản lượng, mặc định sắp xếp ngày mới nhất lên đầu.
    Sử dụng joinedload để lấy luôn thông tin Product đi kèm.
    """
    return (
        db.query(WeavingDailyProduction)
        .options(joinedload(WeavingDailyProduction.product)) # Eager load Product
        .order_by(desc(WeavingDailyProduction.date))         # Sắp xếp ngày giảm dần
        .offset(skip)
        .limit(limit)
        .all()
    )


# =========================
# GET ONE (BY ID)
# =========================
def get_production(db: Session, production_id: int):
    return (
        db.query(WeavingDailyProduction)
        .options(joinedload(WeavingDailyProduction.product))
        .filter(WeavingDailyProduction.id == production_id)
        .first()
    )


# =========================
# SEARCH ADVANCED (TỪ KHÓA / KHOẢNG NGÀY / SẢN PHẨM)
# =========================
def search_productions(
    db: Session,
    keyword: str | None = None,     # Tìm theo Mã sản phẩm (item_code)
    product_id: int | None = None,  # Lọc chính xác theo ID sản phẩm
    from_date: date | None = None,  # Lọc từ ngày
    to_date: date | None = None,    # Lọc đến ngày
    skip: int = 0,
    limit: int = 100
):
    # Bắt đầu query và Join với bảng Product để tìm kiếm theo tên/mã sản phẩm
    query = db.query(WeavingDailyProduction).join(WeavingDailyProduction.product)

    # 1. Lọc theo từ khóa (Áp dụng lên Mã sản phẩm hoặc Ghi chú sản phẩm)
    if keyword:
        keyword_filter = f"%{keyword}%"
        query = query.filter(
            or_(
                Product.item_code.ilike(keyword_filter),
                Product.note.ilike(keyword_filter)
            )
        )

    # 2. Lọc chính xác theo Product ID (thường dùng cho Dropdown filter)
    if product_id:
        query = query.filter(WeavingDailyProduction.product_id == product_id)

    # 3. Lọc theo khoảng thời gian (Từ ngày... Đến ngày...)
    if from_date:
        query = query.filter(WeavingDailyProduction.date >= from_date)
    
    if to_date:
        query = query.filter(WeavingDailyProduction.date <= to_date)

    # Trả về kết quả (Sắp xếp ngày mới nhất trước)
    return (
        query
        .options(joinedload(WeavingDailyProduction.product)) # Load dữ liệu bảng Product để hiển thị UI
        .order_by(desc(WeavingDailyProduction.date))
        .offset(skip)
        .limit(limit)
        .all()
    )


# =========================
# CREATE
# =========================
def create_production(db: Session, data: WeavingProductionCreate):
    # Lưu ý: Model có UniqueConstraint(date, product_id), nếu trùng sẽ raise IntegrityError.
    # Controller nên try/catch lỗi này.
    production = WeavingDailyProduction(**data.model_dump())
    db.add(production)
    db.commit()
    db.refresh(production)
    return production


# =========================
# UPDATE (PATCH STYLE)
# =========================
def update_production(
    db: Session,
    production_id: int,
    data: WeavingProductionUpdate
):
    production = get_production(db, production_id)
    if not production:
        return None

    # exclude_unset=True: Chỉ update những trường client gửi lên
    update_data = data.model_dump(exclude_unset=True)

    for k, v in update_data.items():
        setattr(production, k, v)

    db.commit()
    db.refresh(production)
    return production


# =========================
# DELETE
# =========================
def delete_production(db: Session, production_id: int):
    production = get_production(db, production_id)
    if not production:
        return False

    db.delete(production)
    db.commit()
    return True

<<<<<<< HEAD
=======
# [BỔ SUNG HÀM NÀY VÀO CUỐI FILE]
>>>>>>> c468be65d7388abd40a800c84aa27cfe56d2c0d3
def calculate_daily_production(db: Session, target_date: date):
    """
    Tính toán lại sản lượng cho một ngày cụ thể dựa trên các phiếu đã hoàn thành.
    """
    print(f"🚀 Starting calculation for date: {target_date}")

    # 1. Xóa dữ liệu cũ của ngày hôm đó để tính lại từ đầu (tránh duplicate/sai lệch)
    # db.query(WeavingDailyProduction).filter(WeavingDailyProduction.date == target_date).delete()
    # db.commit()
    # (Optional: Nếu muốn clean sạch sẽ trước khi tính. Nếu dùng logic update bên dưới thì ko cần delete)

    # 2. Query Aggregate từ bảng WeavingBasketTicket
    results = (
        db.query(
            WeavingBasketTicket.product_id,
            func.sum(WeavingBasketTicket.net_weight).label("total_kg"),
            func.sum(WeavingBasketTicket.length_meters).label("total_meters"),
            func.count(distinct(WeavingBasketTicket.machine_id)).label("active_lines") 
        )
        .filter(
            WeavingBasketTicket.time_out.isnot(None), # Chỉ tính phiếu đã xong
            cast(WeavingBasketTicket.time_out, Date) == target_date # Lọc theo ngày ra
        )
        .group_by(WeavingBasketTicket.product_id)
        .all()
    )

    if not results:
        print("⚠️ No finished tickets found for this date.")
        return {"message": f"No data found for {target_date}"}

    # 3. Lưu vào bảng WeavingDailyProduction
    count_updated = 0
    for row in results:
        # Tìm bản ghi cũ
        daily_record = (
            db.query(WeavingDailyProduction)
            .filter(
                WeavingDailyProduction.date == target_date,
                WeavingDailyProduction.product_id == row.product_id
            )
            .first()
        )

        if daily_record:
            # Update
            daily_record.total_kg = row.total_kg or 0
            daily_record.total_meters = row.total_meters or 0
            daily_record.active_machine_lines = row.active_lines or 0
        else:
            # Create
            new_record = WeavingDailyProduction(
                date=target_date,
                product_id=row.product_id,
                total_kg=row.total_kg or 0,
                total_meters=row.total_meters or 0,
                active_machine_lines=row.active_lines or 0
            )
            db.add(new_record)
        count_updated += 1
    
    db.commit()
    print(f"✅ Successfully updated {count_updated} records.")
    return {"message": f"Updated {count_updated} products for {target_date}"}