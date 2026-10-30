from sqlalchemy import Column, ForeignKey, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class SalesRequestBase(BaseModel):
    request_number: str
    customer_id: UUID

    service_type: str
    service_sub_type: str | None = None
    people_count: int | None = Field(default=None, ge=1)

    # Matches the existing database column "buget".
    buget: Decimal | None = Field(default=None, ge=0)
    currency: str | None = None

    departure: str | None = None
    destination: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    trip_type: str | None = None

    additional_requirements: str | None = None
    customer_details: dict[str, Any] | None = None
    service_details: dict[str, Any] | None = None
    request_mode: str | None = None

    @model_validator(mode="after")
    def validate_dates(self):
        if (
            self.start_date is not None
            and self.end_date is not None
            and self.end_date < self.start_date
        ):
            raise ValueError(
                "end_date cannot be earlier than start_date"
            )
        return self


class SalesRequestCreate(SalesRequestBase):
    pass


class SalesRequestUpdate(BaseModel):
    service_type: str | None = None
    service_sub_type: str | None = None
    people_count: int | None = Field(default=None, ge=1)

    buget: Decimal | None = Field(default=None, ge=0)
    currency: str | None = None

    departure: str | None = None
    destination: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    trip_type: str | None = None

    additional_requirements: str | None = None
    customer_details: dict[str, Any] | None = None
    service_details: dict[str, Any] | None = None
    request_mode: str | None = None

    model_config = ConfigDict(extra="forbid")


class SalesRequestResponse(SalesRequestBase):
    id: UUID
    # The live SALES_REQUESTS_HJ table has no status column; status is derived
    # from the latest REQUEST_STATUS_HISTORY_HJ entry.
    status: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


from enum import Enum


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


class LegacyAviationRequestResponse(BaseModel):
    request_id: str
    customer_id: str
    request_type: str | None = "BOOKING"
    email: str | None = None
    mobile: str | None = None
    customer_name: str | None = None
    customer_email: str | None = None
    customer_mobile: str | None = None
    status: RequestStatus
    service: str
    passengers: int
    event_flight_details: dict[str, Any] | None = None
    customer_details: dict[str, Any] | None = None


class SalesRequestStatusUpdate(BaseModel):
    status: RequestStatus
