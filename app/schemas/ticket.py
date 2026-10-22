from datetime import datetime
from typing import Optional, List, Union
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class TicketCreate(BaseModel):
    """Schema for submitting a support ticket."""
    subject: str = Field(..., min_length=1, description="Subject of the support ticket")
    message: str = Field(..., min_length=1, description="Detailed message for the support ticket")
    request_id: Optional[str] = Field(None, description="Optional linked request ID (e.g. HJ-01023)")
    request_role: Optional[str] = Field("SALES", description="Role of the creator (default: SALES)")


class Ticket(BaseModel):
    """Unified Schema for a support ticket representation supporting UUID and legacy IDs."""
    id: Union[UUID, str, int] = Field(..., description="Ticket identifier (UUID)")
    ticket_id: Optional[str] = Field(None, description="Formatted ticket ID or UUID")
    request_id: Optional[str] = Field(None, description="Associated aviation request ID")
    request_role: Optional[str] = Field("SALES", description="Role of the requester")
    subject: str = Field(..., description="Ticket subject")
    message: str = Field(..., description="Ticket message")
    status: str = Field(default="OPEN", description="Ticket status (OPEN, IN_PROGRESS, RESOLVED, CLOSED)")
    admin_response: Optional[str] = Field(None, description="Admin team reply or response")
    reply: Optional[str] = Field(None, description="Backwards-compatible alias for admin reply")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    customer_id: Optional[str] = Field(None, description="Salesperson identifier")
    customer_name: Optional[str] = Field(None, description="Salesperson name")

    model_config = ConfigDict(from_attributes=True)


class TicketListResponse(BaseModel):
    """Schema for listing tickets with count."""
    total_count: int = Field(..., description="Total number of tickets")
    tickets: List[Ticket] = Field(default_factory=list, description="List of tickets")
