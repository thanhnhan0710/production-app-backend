from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

from app.api import deps
from app.schemas.inventory_semi_schema import (
    ImportTicketResponse, ImportTicketCreate,
    ExportTicketResponse, ExportTicketCreate,
    ImportDetailResponse
)
from app.services import inventory_semi_service

router = APIRouter()

# =================================================================
# 1. INVENTORY (TỒN KHO)
# =================================================================

@router.get("/inventory", response_model=List[ImportDetailResponse], tags=["Semi-Finished Inventory"])
def read_inventory(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db)
):
    """
    Get list of items currently IN STOCK.
    (These are items that have been imported but not yet exported).
    """
    return inventory_semi_service.get_inventory(db, skip, limit)


# =================================================================
# 2. IMPORT TICKETS (NHẬP KHO)
# =================================================================

@router.get("/imports", response_model=List[ImportTicketResponse], tags=["Semi-Finished Imports"])
def read_import_tickets(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db)
):
    """
    List all Import Tickets (History of goods coming in).
    """
    return inventory_semi_service.get_import_tickets(db, skip, limit)


@router.get("/imports/{ticket_id}", response_model=ImportTicketResponse, tags=["Semi-Finished Imports"])
def read_import_ticket(
    ticket_id: int,
    db: Session = Depends(deps.get_db)
):
    """
    Get details of a specific Import Ticket.
    """
    ticket = inventory_semi_service.get_import_ticket_by_id(db, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Import ticket not found")
    return ticket


@router.post("/imports", response_model=ImportTicketResponse, tags=["Semi-Finished Imports"])
def create_import_ticket(
    ticket_in: ImportTicketCreate,
    db: Session = Depends(deps.get_db)
):
    """
    Create a new Import Ticket.
    - Validates that the Weaving Ticket exists.
    - Validates that the item is NOT already IN_STOCK (prevents double entry).
    """
    return inventory_semi_service.create_import_ticket(db, ticket_in)


# =================================================================
# 3. EXPORT TICKETS (XUẤT KHO)
# =================================================================

@router.get("/exports", response_model=List[ExportTicketResponse], tags=["Semi-Finished Exports"])
def read_export_tickets(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db)
):
    """
    List all Export Tickets (History of goods going out).
    """
    return inventory_semi_service.get_export_tickets(db, skip, limit)


@router.get("/exports/{ticket_id}", response_model=ExportTicketResponse, tags=["Semi-Finished Exports"])
def read_export_ticket(
    ticket_id: int,
    db: Session = Depends(deps.get_db)
):
    """
    Get details of a specific Export Ticket.
    """
    ticket = inventory_semi_service.get_export_ticket_by_id(db, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Export ticket not found")
    return ticket


@router.post("/exports", response_model=ExportTicketResponse, tags=["Semi-Finished Exports"])
def create_export_ticket(
    ticket_in: ExportTicketCreate,
    db: Session = Depends(deps.get_db)
):
    """
    Create a new Export Ticket.
    - Validates that the item is currently IN_STOCK.
    - Automatically updates the item's status to EXPORTED (deducts from inventory).
    """
    return inventory_semi_service.create_export_ticket(db, ticket_in)