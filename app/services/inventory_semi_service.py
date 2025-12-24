from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from fastapi import HTTPException
from datetime import datetime
from typing import List, Optional

from app.models.inventory_semi import (
    SemiFinishedImportTicket, SemiFinishedImportDetail,
    SemiFinishedExportTicket, SemiFinishedExportDetail,
    StockStatus, ExportReason
)
from app.models.weaving_basket_ticket import WeavingBasketTicket
from app.schemas.inventory_semi_schema import (
    ImportTicketCreate, ExportTicketCreate
)

# =======================================================
# A. IMPORT SERVICES (NHẬP KHO)
# =======================================================

def get_import_tickets(db: Session, skip: int = 0, limit: int = 100):
    return (
        db.query(SemiFinishedImportTicket)
        .order_by(desc(SemiFinishedImportTicket.import_date))
        .offset(skip)
        .limit(limit)
        .all()
    )

def get_import_ticket_by_id(db: Session, ticket_id: int):
    return db.query(SemiFinishedImportTicket).filter(SemiFinishedImportTicket.id == ticket_id).first()

def create_import_ticket(db: Session, ticket_in: ImportTicketCreate):
    # 1. Check duplicate Code
    if db.query(SemiFinishedImportTicket).filter(SemiFinishedImportTicket.code == ticket_in.code).first():
        raise HTTPException(status_code=409, detail=f"Import Ticket code '{ticket_in.code}' already exists.")

    # 2. Create Header
    db_ticket = SemiFinishedImportTicket(
        code=ticket_in.code,
        import_date=ticket_in.import_date or datetime.now(),
        employee_id=ticket_in.employee_id
    )
    db.add(db_ticket)
    db.flush() # Flush to get ID

    # 3. Process Details
    for detail_in in ticket_in.details:
        # Check if Weaving Ticket exists
        weaving_ticket = db.query(WeavingBasketTicket).filter(WeavingBasketTicket.id == detail_in.weaving_ticket_id).first()
        if not weaving_ticket:
            raise HTTPException(status_code=404, detail=f"Weaving Ticket ID {detail_in.weaving_ticket_id} not found.")

        # Check Logic: Is this item already IN_STOCK?
        # Tìm xem rổ này có đang nằm trong ImportDetail nào mà status = IN_STOCK không
        existing_stock = db.query(SemiFinishedImportDetail).filter(
            SemiFinishedImportDetail.weaving_ticket_id == detail_in.weaving_ticket_id,
            SemiFinishedImportDetail.status == StockStatus.IN_STOCK
        ).first()

        if existing_stock:
             raise HTTPException(
                status_code=409, 
                detail=f"Weaving Ticket ID {detail_in.weaving_ticket_id} is already IN_STOCK (Import ID: {existing_stock.import_ticket_id})."
            )

        # Add Detail
        db_detail = SemiFinishedImportDetail(
            import_ticket_id=db_ticket.id,
            weaving_ticket_id=detail_in.weaving_ticket_id,
            warehouse_location=detail_in.warehouse_location,
            note=detail_in.note,
            status=StockStatus.IN_STOCK
        )
        db.add(db_detail)

    db.commit()
    db.refresh(db_ticket)
    return db_ticket


# =======================================================
# B. EXPORT SERVICES (XUẤT KHO)
# =======================================================

def get_export_tickets(db: Session, skip: int = 0, limit: int = 100):
    return (
        db.query(SemiFinishedExportTicket)
        .order_by(desc(SemiFinishedExportTicket.export_date))
        .offset(skip)
        .limit(limit)
        .all()
    )

def get_export_ticket_by_id(db: Session, ticket_id: int):
    return db.query(SemiFinishedExportTicket).filter(SemiFinishedExportTicket.id == ticket_id).first()

def create_export_ticket(db: Session, ticket_in: ExportTicketCreate):
    """
    Quy trình xuất kho:
    1. Tạo phiếu xuất.
    2. Với mỗi chi tiết:
       - Kiểm tra xem rổ đó có đang IN_STOCK trong bảng ImportDetail không.
       - Nếu có: 
           + Tạo dòng ExportDetail.
           + Cập nhật dòng ImportDetail tương ứng thành EXPORTED (Trừ kho).
       - Nếu không: Báo lỗi.
    """
    # 1. Check duplicate Code
    if db.query(SemiFinishedExportTicket).filter(SemiFinishedExportTicket.code == ticket_in.code).first():
        raise HTTPException(status_code=409, detail=f"Export Ticket code '{ticket_in.code}' already exists.")

    # 2. Create Header
    db_ticket = SemiFinishedExportTicket(
        code=ticket_in.code,
        export_date=ticket_in.export_date or datetime.now(),
        employee_id=ticket_in.employee_id,
        reason=ticket_in.reason
    )
    db.add(db_ticket)
    db.flush()

    # 3. Process Details
    for detail_in in ticket_in.details:
        # Tìm rổ hàng này trong kho (phải là IN_STOCK)
        stock_item = db.query(SemiFinishedImportDetail).filter(
            SemiFinishedImportDetail.weaving_ticket_id == detail_in.weaving_ticket_id,
            SemiFinishedImportDetail.status == StockStatus.IN_STOCK
        ).first()

        if not stock_item:
            raise HTTPException(
                status_code=400, 
                detail=f"Weaving Ticket ID {detail_in.weaving_ticket_id} is not available in stock (Cannot export)."
            )

        # A. Tạo chi tiết xuất
        db_export_detail = SemiFinishedExportDetail(
            export_ticket_id=db_ticket.id,
            weaving_ticket_id=detail_in.weaving_ticket_id,
            status=StockStatus.EXPORTED,
            note=detail_in.note
        )
        db.add(db_export_detail)

        # B. Cập nhật trạng thái trong kho -> EXPORTED (Để không xuất được nữa)
        stock_item.status = StockStatus.EXPORTED
        # Không cần add stock_item vì nó đã được track bởi session khi query

    db.commit()
    db.refresh(db_ticket)
    return db_ticket

# =======================================================
# C. INVENTORY SERVICE (TỒN KHO)
# =======================================================

def get_inventory(db: Session, skip: int = 0, limit: int = 100):
    """Lấy danh sách các rổ đang tồn trong kho (IN_STOCK)"""
    return (
        db.query(SemiFinishedImportDetail)
        .filter(SemiFinishedImportDetail.status == StockStatus.IN_STOCK)
        .order_by(desc(SemiFinishedImportDetail.id))
        .offset(skip)
        .limit(limit)
        .all()
    )