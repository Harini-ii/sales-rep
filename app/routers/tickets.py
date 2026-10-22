import uuid
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Response, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.schemas.ticket import TicketCreate, Ticket, TicketListResponse
from app.models.ticket import SupportTicket, SupportTicketHJ
from app.database import get_db
from app.data import mock_data

router = APIRouter(
    prefix="/tickets",
    tags=["Support Tickets"]
)


def _get_current_salesperson() -> tuple[str, str]:
    """
    Retrieves the current salesperson identity from the backend profile context.
    Does NOT trust client-supplied parameters for identity.
    """
    email = mock_data.profile_db.get("email") or "abhi@gmail.com"
    full_name = mock_data.profile_db.get("full_name") or "Sales Representative"
    return email.strip(), full_name.strip()


def _to_support_ticket_hj_response(record: SupportTicketHJ) -> Ticket:
    """Helper to convert SupportTicketHJ (UUID) to unified Ticket response schema."""
    uuid_str = str(record.id)
    return Ticket(
        id=uuid_str,
        ticket_id=uuid_str,
        request_id=record.request_id,
        request_role=record.request_role or "SALES",
        subject=record.subject,
        message=record.message,
        status=record.status or "OPEN",
        admin_response=record.admin_response,
        reply=record.admin_response,
        created_at=record.created_at,
        updated_at=record.updated_at
    )


def _to_legacy_ticket_response(record: SupportTicket) -> Ticket:
    """Helper to convert legacy SupportTicket to unified Ticket response schema."""
    return Ticket(
        id=record.id,
        ticket_id=f"SUP-{record.id:03d}",
        request_id=None,
        request_role="SALES",
        subject=record.subject,
        message=record.message,
        status=record.status or "OPEN",
        admin_response=record.reply,
        reply=record.reply,
        created_at=record.created_at,
        updated_at=record.updated_at,
        customer_id=record.customer_id,
        customer_name=record.customer_name
    )


@router.post("/", response_model=Ticket, status_code=status.HTTP_201_CREATED)
def create_ticket(ticket_data: TicketCreate, db: Session = Depends(get_db)):
    """
    Create a new support ticket in sales_hj.support_ticket_hj.
    Generates a unique UUID for ticket ID and initializes status to OPEN.
    """
    now = datetime.now(timezone.utc)
    assigned_request_id = ticket_data.request_id.strip() if ticket_data.request_id else str(uuid.uuid4())
    new_ticket = SupportTicketHJ(
        id=uuid.uuid4(),
        request_id=assigned_request_id,
        request_role=ticket_data.request_role.strip() if ticket_data.request_role else "SALES",
        subject=ticket_data.subject.strip(),
        message=ticket_data.message.strip(),
        status="OPEN",
        admin_response=None,
        created_at=now,
        updated_at=now
    )

    try:
        db.add(new_ticket)
        db.commit()
        db.refresh(new_ticket)
        return _to_support_ticket_hj_response(new_ticket)
    except SQLAlchemyError as db_err:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error creating support ticket: {str(db_err)}"
        )


@router.get("/", response_model=TicketListResponse, status_code=status.HTTP_200_OK)
def get_tickets(response: Response, db: Session = Depends(get_db)):
    """
    Retrieve support tickets from sales_hj.support_ticket_hj (and legacy records).
    Returns total ticket count and details including UUIDs, status, timestamps, and Admin responses.
    """
    try:
        # 1. Fetch tickets from new UUID table sales_hj.support_ticket_hj
        new_records = (
            db.query(SupportTicketHJ)
            .order_by(SupportTicketHJ.created_at.desc())
            .all()
        )
        ticket_items = [_to_support_ticket_hj_response(r) for r in new_records]

        # 2. Also include any legacy records from support_tickets_hj
        legacy_records = (
            db.query(SupportTicket)
            .order_by(SupportTicket.created_at.desc())
            .all()
        )
        for lr in legacy_records:
            ticket_items.append(_to_legacy_ticket_response(lr))

        total_count = len(ticket_items)
        response.headers["X-Total-Count"] = str(total_count)

        return TicketListResponse(
            total_count=total_count,
            tickets=ticket_items
        )
    except SQLAlchemyError as db_err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error retrieving support tickets: {str(db_err)}"
        )


@router.get("/{ticket_id}", response_model=Ticket, status_code=status.HTTP_200_OK)
def get_ticket_by_id(ticket_id: str, db: Session = Depends(get_db)):
    """
    Retrieve details of a specific ticket by its UUID (or legacy ID).
    """
    clean_id = ticket_id.strip()

    # 1. Try matching UUID in sales_hj.support_ticket_hj
    try:
        parsed_uuid = uuid.UUID(clean_id)
        record = db.query(SupportTicketHJ).filter(SupportTicketHJ.id == parsed_uuid).first()
        if record:
            return _to_support_ticket_hj_response(record)
    except (ValueError, AttributeError):
        pass

    # 2. Try matching legacy ID or SUP-xxx in sales_hj.support_tickets_hj
    parsed_id: Optional[int] = None
    if clean_id.upper().startswith("SUP-"):
        try:
            parsed_id = int(clean_id[4:])
        except ValueError:
            pass
    elif clean_id.isdigit():
        parsed_id = int(clean_id)

    if parsed_id is not None:
        try:
            legacy_record = db.query(SupportTicket).filter(SupportTicket.id == parsed_id).first()
            if legacy_record:
                return _to_legacy_ticket_response(legacy_record)
        except SQLAlchemyError:
            pass

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Ticket '{ticket_id}' not found"
    )
