from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.api import deps
from app.schemas.weaving_basket_ticket_schema import (
    WeavingTicketResponse,
    WeavingTicketCreate,
    WeavingTicketUpdate
)
from app.services import weaving_basket_ticket_service

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
    Useful for filtering:
    - All tickets by a specific machine.
    - All tickets handled by a specific employee.
    - Tickets that are currently in progress (is_finished=False).
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
    db: Session = Depends(deps.get_db)
):
    """
    Create a new weaving ticket (Start process).
    - Requires: Code, Product, Standard, Machine, Yarn info, Basket, Employee In.
    - Checks for duplicate Code.
    """
    return weaving_basket_ticket_service.create_ticket(db, ticket_in)


# =========================
# UPDATE (Quy trình: Ra rổ / Finish)
# =========================
@router.put("/{ticket_id}", response_model=WeavingTicketResponse)
def update_weaving_ticket(
    ticket_id: int,
    ticket_in: WeavingTicketUpdate,
    db: Session = Depends(deps.get_db)
):
    """
    Update ticket info. Commonly used for the 'Finish' process (Ra rổ).
    - If 'gross_weight' is provided, the system AUTOMATICALLY calculates 'net_weight' 
      based on the Basket's tare weight.
    - Can also be used to correct initial data.
    """
    return weaving_basket_ticket_service.update_ticket(db, ticket_id, ticket_in)


# =========================
# DELETE
# =========================
@router.delete("/{ticket_id}")
def delete_weaving_ticket(
    ticket_id: int,
    db: Session = Depends(deps.get_db)
):
    """
    Delete a weaving ticket.
    """
    return weaving_basket_ticket_service.delete_ticket(db, ticket_id)