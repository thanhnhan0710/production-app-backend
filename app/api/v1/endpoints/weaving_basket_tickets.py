from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks # [MỚI] Thêm BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional

from app.api import deps
from app.schemas.weaving_basket_ticket_schema import (
    WeavingTicketResponse,
    WeavingTicketCreate,
    WeavingTicketUpdate
)
from app.services import weaving_basket_ticket_service
from app.core.websockets import ws_manager # [MỚI] Import WebSocket Manager

router = APIRouter()

# =========================
# GET LIST (Mới nhất lên đầu)
# =========================
@router.get("/", response_model=List[WeavingTicketResponse])
def read_weaving_tickets(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db)
):
    """
    Get list of weaving basket tickets (paginated, sorted by newest).
    """
    return weaving_basket_ticket_service.get_tickets(db, skip, limit)


# =========================
# SEARCH (Tìm kiếm & Lọc)
# =========================
@router.get("/search", response_model=List[WeavingTicketResponse])
def search_weaving_tickets(
    code: Optional[str] = None,
    product_id: Optional[int] = None,
    machine_id: Optional[int] = None,
    employee_id: Optional[int] = Query(None, description="Search by Employee (In OR Out)"),
    is_finished: Optional[bool] = Query(None, description="True: Finished (Has Time Out), False: In Progress"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db)
):
    """
    Advanced search for tickets.
    """
    return weaving_basket_ticket_service.search_tickets(
        db=db,
        code=code,
        product_id=product_id,
        machine_id=machine_id,
        employee_id=employee_id,
        is_finished=is_finished,
        skip=skip,
        limit=limit
    )


# =========================
# GET DETAIL
# =========================
@router.get("/{ticket_id}", response_model=WeavingTicketResponse)
def read_weaving_ticket(
    ticket_id: int,
    db: Session = Depends(deps.get_db)
):
    """
    Get specific ticket details by ID.
    """
    ticket = weaving_basket_ticket_service.get_ticket_by_id(db, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Weaving basket ticket not found")
    return ticket


# =========================
# CREATE (Quy trình: Vào rổ / Start)
# =========================
@router.post("/", response_model=WeavingTicketResponse)
def create_weaving_ticket(
    ticket_in: WeavingTicketCreate,
    background_tasks: BackgroundTasks, # [MỚI]
    db: Session = Depends(deps.get_db)
):
    """
    Create a new weaving ticket (Start process).
    """
    new_ticket = weaving_basket_ticket_service.create_ticket(db, ticket_in)
    
    # [MỚI] Bắn tín hiệu WebSocket
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_WEAVING_TICKETS")
    return new_ticket


# =========================
# UPDATE (Quy trình: Ra rổ / Finish)
# =========================
@router.put("/{ticket_id}", response_model=WeavingTicketResponse)
def update_weaving_ticket(
    ticket_id: int,
    ticket_in: WeavingTicketUpdate,
    background_tasks: BackgroundTasks, # [MỚI]
    db: Session = Depends(deps.get_db)
):
    """
    Update ticket info. Commonly used for the 'Finish' process (Ra rổ).
    """
    updated_ticket = weaving_basket_ticket_service.update_ticket(db, ticket_id, ticket_in)
    
    # [MỚI] Bắn tín hiệu WebSocket
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_WEAVING_TICKETS")
    return updated_ticket


# =========================
# DELETE
# =========================
@router.delete("/{ticket_id}")
def delete_weaving_ticket(
    ticket_id: int,
    background_tasks: BackgroundTasks, # [MỚI]
    db: Session = Depends(deps.get_db)
):
    """
    Delete a weaving ticket.
    """
    result = weaving_basket_ticket_service.delete_ticket(db, ticket_id)
    
    # [MỚI] Bắn tín hiệu WebSocket
    background_tasks.add_task(ws_manager.broadcast, "REFRESH_WEAVING_TICKETS")
    return result