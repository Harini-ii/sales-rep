from enum import Enum
from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any

class RequestStatus(str, Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    SALES_CONTACTED = "SALES_CONTACTED"
    OPTIONS_FOUND = "OPTIONS_FOUND"
    QUOTE_SENT = "QUOTE_SENT"
    BOOKED = "BOOKED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class EventFlightDetails(BaseModel):
    event_type: Optional[str] = "Not provided"
    timing: Optional[str] = "Not provided"
    date: Optional[str] = "Not provided"
    time: Optional[str] = "Not provided"
    aircraft: Optional[str] = "Not provided"
    aircraft_type: Optional[str] = "Not provided"
    capacity: Optional[str] = "Not provided"
    food: Optional[str] = "Not provided"
    drinks: Optional[str] = "Not provided"
    champagne: Optional[str] = "Not requested"
    crew_preferences: Optional[str] = "Not provided"

    model_config = ConfigDict(from_attributes=True)

class CustomerDetails(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class AviationRequest(BaseModel):
    request_id: str
    customer_id: str
    request_type: Optional[str] = "BOOKING"
    email: Optional[str] = None
    mobile: Optional[str] = None
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    customer_mobile: Optional[str] = None
    status: RequestStatus
    service: str
    passengers: int
    event_flight_details: Optional[EventFlightDetails] = None
    customer_details: Optional[CustomerDetails] = None

    model_config = ConfigDict(from_attributes=True)

class AviationRequestCreate(BaseModel):
    request_id: Optional[str] = None
    customer_id: str
    request_type: Optional[str] = "BOOKING"
    service: str = "AVIATION"
    status: Optional[RequestStatus] = RequestStatus.DRAFT
    passengers: Optional[int] = 1
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    customer_mobile: Optional[str] = None
    event_flight_details: Optional[EventFlightDetails] = None
    customer_details: Optional[CustomerDetails] = None

class AviationRequestUpdate(BaseModel):
    status: RequestStatus

class AviationRequestStatusResponse(BaseModel):
    request_id: str
    status: RequestStatus
    message: str

