import logging
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from fastapi import HTTPException
from typing import Optional
from datetime import datetime

# Import Models & Schemas
from app.models.weaving_basket_ticket import WeavingBasketTicket
from app.models.basket import Basket  # Cần import để lấy tare_weight
from app.schemas.weaving_basket_ticket_schema import WeavingTicketCreate, WeavingTicketUpdate
from app.services import weaving_daily_production_service

logger = logging.getLogger(__name__)

# ============================
# READ (Get Data)
# ============================

def get_ticket_by_id(db: Session, ticket_id: int):
    return db.query(WeavingBasketTicket).filter(WeavingBasketTicket.id == ticket_id).first()

def get_ticket_by_code(db: Session, code: str):
    return db.query(WeavingBasketTicket).filter(WeavingBasketTicket.code == code).first()

def get_tickets(db: Session, skip: int = 0, limit: int = 100):
    """Lấy danh sách phiếu, mới nhất lên đầu"""
    return (
        db.query(WeavingBasketTicket)
        .order_by(desc(WeavingBasketTicket.id))
        .offset(skip)
        .limit(limit)
        .all()
    )

# ============================
# SEARCH / FILTER
# ============================

def search_tickets(
    db: Session,
    code: Optional[str] = None,
    product_id: Optional[int] = None,
    machine_id: Optional[int] = None,
    employee_id: Optional[int] = None, # Tìm cả người vào hoặc ra
    is_finished: Optional[bool] = None, # True: Đã ra rổ, False: Đang chạy
    skip: int = 0,
    limit: int = 100
):
    query = db.query(WeavingBasketTicket)

    if code:
        query = query.filter(WeavingBasketTicket.code.ilike(f"%{code}%"))
    
    if product_id:
        query = query.filter(WeavingBasketTicket.product_id == product_id)
        
    if machine_id:
        query = query.filter(WeavingBasketTicket.machine_id == machine_id)

    if employee_id:
        # Tìm phiếu mà nhân viên này tham gia (Vào hoặc Ra)
        query = query.filter(
            (WeavingBasketTicket.employee_in_id == employee_id) |
            (WeavingBasketTicket.employee_out_id == employee_id)
        )

    if is_finished is not None:
        if is_finished:
            query = query.filter(WeavingBasketTicket.time_out.isnot(None))
        else:
            query = query.filter(WeavingBasketTicket.time_out.is_(None))

    return query.order_by(desc(WeavingBasketTicket.id)).offset(skip).limit(limit).all()

# ============================
# CREATE (Bắt đầu phiếu)
# ============================

def create_ticket(db: Session, ticket_in: WeavingTicketCreate):
    # 1. Check duplicate code
    if get_ticket_by_code(db, ticket_in.code):
        raise HTTPException(status_code=409, detail=f"Ticket code '{ticket_in.code}' already exists.")

    # 2. Logic kiểm tra rổ (Optional):
    # Rổ phải ở trạng thái READY mới được dùng. 
    # Nếu rổ đang IN_USE ở phiếu khác chưa đóng thì không được tạo.
    # (Bạn có thể thêm logic check bảng Basket ở đây)

    # 3. Create
    db_ticket = WeavingBasketTicket(**ticket_in.model_dump())
    
    # Set default time_in if not provided
    if not db_ticket.time_in:
        db_ticket.time_in = datetime.now()

    db.add(db_ticket)
    db.commit()
    db.refresh(db_ticket)
    
    # 4. Update status Basket -> IN_USE (Nếu cần thiết)
    basket = db.query(Basket).get(ticket_in.basket_id)
    basket.status = "IN_USE"
    db.commit()
    
    return db_ticket

# ============================
# UPDATE (Ra rổ / Hoàn thành)
# ============================

def update_ticket(db: Session, ticket_id: int, ticket_in: WeavingTicketUpdate):
    # 1. Tìm phiếu rổ
    db_ticket = db.query(WeavingBasketTicket).filter(WeavingBasketTicket.id == ticket_id).first()
    if not db_ticket:
        raise HTTPException(status_code=404, detail="Weaving Ticket not found")

    # 2. Logic tính Net Weight tự động (Trọng lượng tịnh)
    # Nếu người dùng nhập Gross Weight (Cả bì), tự động trừ Tare Weight (Trọng lượng rổ)
    if ticket_in.gross_weight is not None:
        # Lấy basket_id mới (nếu user đổi rổ) hoặc dùng basket_id cũ
        current_basket_id = ticket_in.basket_id if ticket_in.basket_id else db_ticket.basket_id
        
        basket = db.query(Basket).filter(Basket.basket_id == current_basket_id).first()
        
        if basket:
            # Net = Gross - Tare. Đảm bảo không âm.
            calculated_net = ticket_in.gross_weight - basket.tare_weight
            ticket_in.net_weight = max(0.0, calculated_net)
        else:
            # Trường hợp hiếm: Không tìm thấy rổ, giữ nguyên net_weight = gross_weight hoặc 0
            ticket_in.net_weight = ticket_in.gross_weight

    # 3. Cập nhật các trường thông tin
    # exclude_unset=True: Chỉ update những trường client gửi lên, không ghi đè NULL vào trường cũ
    update_data = ticket_in.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(db_ticket, field, value)

    # 4. Tự động điền giờ ra (time_out) nếu chưa có
    # Logic: Nếu có update khối lượng hoặc người ra -> coi như hoàn thành
    if (ticket_in.employee_out_id or ticket_in.gross_weight) and not db_ticket.time_out:
        db_ticket.time_out = datetime.now()

    # 5. Cập nhật trạng thái Rổ (Basket Status)
    # Nếu phiếu đã hoàn thành (có time_out), trả rổ về trạng thái READY để tái sử dụng
    if db_ticket.time_out:
        basket = db.query(Basket).filter(Basket.basket_id == db_ticket.basket_id).first()
        if basket and basket.status != "READY":
            basket.status = "READY"
            # Hoặc "HOLDING" nếu quy trình là phải nhập kho xong mới Ready
            # basket.status = "HOLDING" 

    # Lưu thay đổi chính vào DB
    try:
        db.commit()
        db.refresh(db_ticket)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database commit error: {str(e)}")

    # ==================================================================
    # 6. [QUAN TRỌNG] TRIGGER TÍNH TOÁN SẢN LƯỢNG NGÀY
    # ==================================================================
    # Chỉ chạy khi phiếu đã hoàn thành (có time_out)
    if db_ticket.time_out:
        try:
            # Lấy ngày ra của phiếu (VD: 2023-10-27)
            target_date = db_ticket.time_out.date()
            
            logger.info(f"🔄 Đang tính lại sản lượng cho ngày: {target_date}")
            
            # Gọi service thống kê để cập nhật bảng weaving_daily_productions
            weaving_daily_production_service.calculate_daily_production(
                db=db, 
                target_date=target_date
            )
        except Exception as e:
            # Log lỗi nhưng KHÔNG raise Exception để tránh rollback transaction phiếu rổ
            # Vì phiếu đã lưu thành công rồi, lỗi thống kê có thể chạy lại sau.
            logger.error(f"⚠️ Lỗi tính toán sản lượng tự động: {e}")
            print(f"⚠️ Error calculating stats: {e}")

    return db_ticket

# ============================
# DELETE
# ============================

def delete_ticket(db: Session, ticket_id: int):
    db_ticket = get_ticket_by_id(db, ticket_id)
    if not db_ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    # Có thể thêm logic: Không cho xóa nếu phiếu đã hoàn thành (có time_out)
    
    db.delete(db_ticket)
    db.commit()
    return {"message": "Ticket deleted successfully"}