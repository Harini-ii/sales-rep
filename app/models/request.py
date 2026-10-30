
import uuid
from datetime import datetime, timezone
from app.database import Base

from sqlalchemy import (
    Column,
    String,
    Integer,
    Date,
    DateTime,
    Numeric,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.database import Base


class SalesRequestHJ(Base):
    """
    Maps to sales_hj."SALES_REQUESTS_HJ".
    Uses id (UUID) as the primary key.
    """

    __tablename__ = "SALES_REQUESTS_HJ"
    __table_args__ = {"schema": "sales_hj"}

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    request_number = Column(String, nullable=False, index=True)
    customer_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    service_type = Column(String, nullable=False)
    service_sub_type = Column(String, nullable=True)
    people_count = Column(Integer, nullable=True)

    # Matches the actual database column spelling.
    buget = Column(Numeric, nullable=True)
    currency = Column(String, nullable=True)

    departure = Column(String, nullable=True)
    destination = Column(String, nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    trip_type = Column(String, nullable=True)

    additional_requirements = Column(Text, nullable=True)
    customer_details = Column(JSONB, nullable=True)
    service_details = Column(JSONB, nullable=True)
    request_mode = Column(String, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        nullable=True,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=True,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class AviationRequestModel(Base):
    """Legacy request table used by HJ-prefixed request IDs."""

    __tablename__ = "REQUESTS_HJ"
    __table_args__ = {"schema": "sales_hj"}

    request_id = Column(String(50), primary_key=True, index=True)
    customer_id = Column(String(255), nullable=False, index=True)
    request_type = Column(String(50), nullable=True, default="BOOKING")
    service = Column(String(100), nullable=False, default="AVIATION")
    status = Column(String(50), nullable=False, default="DRAFT", index=True)
    passengers = Column(Integer, default=1)
    customer_name = Column(String(255), nullable=True)
    customer_email = Column(String(255), nullable=True)
    customer_mobile = Column(String(50), nullable=True)
    event_flight_details = Column(JSONB, nullable=True)
    customer_details = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=True)


class RequestStatusHistoryModel(Base):
    """
    Maps to sales_hj."REQUEST_STATUS_HISTORY_HJ".
    Stores request status transitions.
    """

    __tablename__ = "REQUEST_STATUS_HISTORY_HJ"
    __table_args__ = {"schema": "sales_hj"}

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # The live table stores the request number/key as VARCHAR(50), not UUID.
    request_id = Column(String(50), nullable=False, index=True)

    old_status = Column(String(50), nullable=True)
    new_status = Column(String(50), nullable=False)
    changed_by = Column(String(255), nullable=True)

    changed_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
