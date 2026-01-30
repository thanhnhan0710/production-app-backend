import logging
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc
from fastapi import HTTPException
from typing import Optional
from datetime import datetime

# Import Models & Schemas
from app.models.material_receipt import MaterialReceipt, MaterialReceiptDetail
from app.models.weaving_basket_ticket import WeavingBasketTicket, WeavingTicketYarn
from app.models.basket import Basket
from app.models.batch import Batch  # Cần import để joinedload hoạt động
from app.schemas.weaving_basket_ticket_schema import WeavingTicketCreate, WeavingTicketUpdate
from app.services import weaving_daily_production_service

logger = logging.getLogger(__name__)

# [HELPER] Hàm tạo query options để load dữ liệu quan hệ (Batch, Supplier)
def _get_ticket_load_options():
    return [
        # Load chuỗi quan hệ: Yarn -> Batch -> ReceiptDetail -> Header -> Supplier
        joinedload(WeavingBasketTicket.yarns)
        .joinedload(WeavingTicketYarn.batch)
        .joinedload(Batch.receipt_detail)
        .joinedload(MaterialReceiptDetail.header)
        .joinedload(MaterialReceipt.supplier),
        
        # Các quan hệ khác giữ nguyên
        joinedload(WeavingBasketTicket.product),
        joinedload(WeavingBasketTicket.basket),
        joinedload(WeavingBasketTicket.employee_in),
        joinedload(WeavingBasketTicket.employee_out),
    ]

# ============================
# READ (GET)
# ============================
def get_ticket_by_id(db: Session, ticket_id: int):
    return db.query(WeavingBasketTicket)\
        .options(*_get_ticket_load_options())\
        .filter(WeavingBasketTicket.id == ticket_id)\
        .first()

def get_ticket_by_code(db: Session, code: str):
    return db.query(WeavingBasketTicket)\
        .options(*_get_ticket_load_options())\
        .filter(WeavingBasketTicket.code == code)\
        .first()

def get_tickets(db: Session, skip: int = 0, limit: int = 100):
    return db.query(WeavingBasketTicket)\
        .options(*_get_ticket_load_options())\
        .order_by(desc(WeavingBasketTicket.id))\
        .offset(skip).limit(limit)\
        .all()

def search_tickets(db: Session, code: Optional[str] = None, product_id: Optional[int] = None, machine_id: Optional[int] = None, employee_id: Optional[int] = None, is_finished: Optional[bool] = None, skip: int = 0, limit: int = 100):
    query = db.query(WeavingBasketTicket).options(*_get_ticket_load_options())
    
    if code: query = query.filter(WeavingBasketTicket.code.ilike(f"%{code}%"))
    if product_id: query = query.filter(WeavingBasketTicket.product_id == product_id)
    if machine_id: query = query.filter(WeavingBasketTicket.machine_id == machine_id)
    if employee_id: query = query.filter((WeavingBasketTicket.employee_in_id == employee_id) | (WeavingBasketTicket.employee_out_id == employee_id))
    
    if is_finished is not None:
        if is_finished: query = query.filter(WeavingBasketTicket.time_out.isnot(None))
        else: query = query.filter(WeavingBasketTicket.time_out.is_(None))
        
    return query.order_by(desc(WeavingBasketTicket.id)).offset(skip).limit(limit).all()

# ============================
# CREATE (Bắt đầu phiếu - Manual)
# ============================
def create_ticket(db: Session, ticket_in: WeavingTicketCreate):
    # Check code unique (dùng hàm query nhẹ, không cần join nhiều)
    exists = db.query(WeavingBasketTicket.id).filter(WeavingBasketTicket.code == ticket_in.code).first()
    if exists:
        raise HTTPException(status_code=409, detail=f"Ticket code '{ticket_in.code}' already exists.")

    # 1. Tạo Header
    ticket_data = ticket_in.model_dump(exclude={'yarns'})
    db_ticket = WeavingBasketTicket(**ticket_data)
    
    if not db_ticket.time_in:
        db_ticket.time_in = datetime.now()

    db.add(db_ticket)
    db.flush()

    # 2. Tạo chi tiết sợi (yarns) nếu có
    if ticket_in.yarns:
        for yarn_in in ticket_in.yarns:
            db_yarn = WeavingTicketYarn(
                ticket_id=db_ticket.id,
                batch_id=yarn_in.batch_id,
                component_type=yarn_in.component_type,
                quantity=yarn_in.quantity,
                note=yarn_in.note
            )
            db.add(db_yarn)

    db.commit()
    # Refresh lại object với đầy đủ quan hệ để trả về frontend hiển thị ngay
    # Lưu ý: db.refresh đôi khi không load eager relations, nên ta query lại cho chắc
    return get_ticket_by_id(db, db_ticket.id)

# ============================
# UPDATE (Ra rổ / Hoàn thành)
# ============================
def update_ticket(db: Session, ticket_id: int, ticket_in: WeavingTicketUpdate):
    db_ticket = db.query(WeavingBasketTicket).filter(WeavingBasketTicket.id == ticket_id).first()
    if not db_ticket:
        raise HTTPException(status_code=404, detail="Weaving Ticket not found")

    # Tính Net Weight
    if ticket_in.gross_weight is not None:
        current_basket_id = ticket_in.basket_id if ticket_in.basket_id else db_ticket.basket_id
        if current_basket_id:
            basket = db.query(Basket).filter(Basket.basket_id == current_basket_id).first()
            if basket:
                calculated_net = ticket_in.gross_weight - basket.tare_weight
                ticket_in.net_weight = max(0.0, calculated_net)
            else:
                ticket_in.net_weight = ticket_in.gross_weight

    # Update Fields
    update_data = ticket_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_ticket, field, value)

    # Auto time_out
    if (ticket_in.employee_out_id or ticket_in.gross_weight) and not db_ticket.time_out:
        db_ticket.time_out = datetime.now()

    # Reset Basket status
    if db_ticket.time_out and db_ticket.basket_id:
        basket = db.query(Basket).filter(Basket.basket_id == db_ticket.basket_id).first()
        if basket and basket.status != "READY":
            basket.status = "READY"
            db.add(basket)

    try:
        db.commit()
        # Trả về full data để cập nhật UI
        return get_ticket_by_id(db, ticket_id)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database commit error: {str(e)}")

    # Trigger Daily Production (Logic phụ, không ảnh hưởng return)
    if db_ticket.time_out:
        try:
            target_date = db_ticket.time_out.date()
            logger.info(f"🔄 Calculating daily production for: {target_date}")
            weaving_daily_production_service.calculate_daily_production(
                db=db, 
                target_date=target_date
            )
        except Exception as e:
            logger.error(f"⚠️ Error calculating stats: {e}")

# ============================
# DELETE
# ============================
def delete_ticket(db: Session, ticket_id: int):
    db_ticket = db.query(WeavingBasketTicket).filter(WeavingBasketTicket.id == ticket_id).first()
    if not db_ticket: 
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Giải phóng rổ nếu phiếu chưa hoàn thành
    if db_ticket.basket_id and not db_ticket.time_out:
         basket = db.query(Basket).get(db_ticket.basket_id)
         if basket:
             basket.status = "READY"
             db.add(basket)

    db.delete(db_ticket)
    db.commit()
    return {"message": "Ticket deleted successfully"}