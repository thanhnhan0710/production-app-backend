import logging
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc
from fastapi import HTTPException
from typing import Optional
from datetime import datetime

# Import Models & Schemas
from app.models.weaving_basket_ticket import WeavingBasketTicket, WeavingTicketYarn
from app.models.basket import Basket
from app.models.batch import Batch
from app.models.material_receipt import MaterialReceiptDetail, MaterialReceipt # Cần để join
from app.schemas.weaving_basket_ticket_schema import WeavingTicketCreate, WeavingTicketUpdate
from app.services import weaving_daily_production_service
from app.models.purchase_order import PurchaseOrderHeader
from app.models.supplier import Supplier

logger = logging.getLogger(__name__)

def _get_base_query(db: Session):
    return db.query(WeavingBasketTicket).options(
        joinedload(WeavingBasketTicket.product),
        joinedload(WeavingBasketTicket.basket),
        joinedload(WeavingBasketTicket.employee_in),
        joinedload(WeavingBasketTicket.employee_out),
        
        # CHUỖI JOIN ĐÚNG:
        joinedload(WeavingBasketTicket.yarns)
            .joinedload(WeavingTicketYarn.batch)
            .joinedload(Batch.receipt_detail)
            .joinedload(MaterialReceiptDetail.header) # -> MaterialReceipt
            .joinedload(MaterialReceipt.po_header)    # -> PurchaseOrderHeader
            .joinedload(PurchaseOrderHeader.vendor)   # -> Supplier (SỬA TẠI ĐÂY)
    )

# ============================
# READ METHODS
# ============================

def get_ticket_by_id(db: Session, ticket_id: int):
    return _get_base_query(db).filter(WeavingBasketTicket.id == ticket_id).first()

def get_ticket_by_code(db: Session, code: str):
    return _get_base_query(db).filter(WeavingBasketTicket.code == code).first()

def get_tickets(db: Session, skip: int = 0, limit: int = 100):
    return _get_base_query(db).order_by(desc(WeavingBasketTicket.id)).offset(skip).limit(limit).all()

def search_tickets(db: Session, code: Optional[str] = None, product_id: Optional[int] = None, 
                   machine_id: Optional[int] = None, employee_id: Optional[int] = None, 
                   is_finished: Optional[bool] = None, skip: int = 0, limit: int = 100):
    
    query = _get_base_query(db)
    
    if code: query = query.filter(WeavingBasketTicket.code.ilike(f"%{code}%"))
    if product_id: query = query.filter(WeavingBasketTicket.product_id == product_id)
    if machine_id: query = query.filter(WeavingBasketTicket.machine_id == machine_id)
    if employee_id: 
        query = query.filter((WeavingBasketTicket.employee_in_id == employee_id) | 
                             (WeavingBasketTicket.employee_out_id == employee_id))
    
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
    if get_ticket_by_code(db, ticket_in.code):
        raise HTTPException(status_code=409, detail=f"Ticket code '{ticket_in.code}' already exists.")

    # 1. Tạo Header
    ticket_data = ticket_in.model_dump(exclude={'yarns'})
    db_ticket = WeavingBasketTicket(**ticket_data)
    
    if not db_ticket.time_in:
        db_ticket.time_in = datetime.now()

    db.add(db_ticket)
    db.flush() # Lấy ID của ticket trước khi tạo yarns

    # 2. Tạo chi tiết sợi
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

    # 3. Cập nhật trạng thái Basket
    if ticket_in.basket_id:
        basket = db.query(Basket).get(ticket_in.basket_id)
        if basket:
            basket.status = "IN_USE"

    db.commit()
    # Sau khi commit, dùng get_ticket_by_id để lấy lại object với đầy đủ JOIN
    return get_ticket_by_id(db, db_ticket.id)

# ============================
# UPDATE (Hoàn thành phiếu)
# ============================

def update_ticket(db: Session, ticket_id: int, ticket_in: WeavingTicketUpdate):
    db_ticket = db.query(WeavingBasketTicket).filter(WeavingBasketTicket.id == ticket_id).first()
    if not db_ticket:
        raise HTTPException(status_code=404, detail="Weaving Ticket not found")

    # Tính Net Weight
    if ticket_in.gross_weight is not None:
        current_basket_id = ticket_in.basket_id or db_ticket.basket_id
        if current_basket_id:
            basket = db.query(Basket).filter(Basket.basket_id == current_basket_id).first()
            if basket:
                calculated_net = ticket_in.gross_weight - basket.tare_weight
                ticket_in.net_weight = max(0.0, calculated_net)
            else:
                ticket_in.net_weight = ticket_in.gross_weight

    # Cập nhật các field
    update_data = ticket_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_ticket, field, value)

    # Tự động ghi nhận thời gian ra (time_out)
    if (ticket_in.employee_out_id or ticket_in.gross_weight) and not db_ticket.time_out:
        db_ticket.time_out = datetime.now()

    # Trả Basket về trạng thái sẵn sàng
    if db_ticket.time_out and db_ticket.basket_id:
        basket = db.query(Basket).filter(Basket.basket_id == db_ticket.basket_id).first()
        if basket:
            basket.status = "READY"

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    # Trigger tính toán sản lượng hàng ngày
    if db_ticket.time_out:
        try:
            weaving_daily_production_service.calculate_daily_production(
                db=db, target_date=db_ticket.time_out.date()
            )
        except Exception as e:
            logger.error(f"⚠️ Production stats error: {e}")

    return get_ticket_by_id(db, db_ticket.id)

# ============================
# DELETE
# ============================

def delete_ticket(db: Session, ticket_id: int):
    db_ticket = db.query(WeavingBasketTicket).filter(WeavingBasketTicket.id == ticket_id).first()
    if not db_ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    db.delete(db_ticket)
    db.commit()
    return {"message": "Ticket deleted successfully"}