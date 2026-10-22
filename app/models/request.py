import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class AviationRequestModel(Base):
    """
    SQLAlchemy ORM Model mapped to sales_hj.REQUESTS_HJ table.
    Stores aviation booking and enquiry requests for the sales dashboard.
    """
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
    event_flight_details = Column(JSON, nullable=True, default=dict)
    customer_details = Column(JSON, nullable=True, default=dict)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class RequestStatusHistoryModel(Base):
    """
    SQLAlchemy ORM Model mapped to sales_hj.REQUEST_STATUS_HISTORY_HJ table.
    Logs each status change performed by sales representatives.
    """
    __tablename__ = "REQUEST_STATUS_HISTORY_HJ"
    __table_args__ = {"schema": "sales_hj"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    request_id = Column(String(50), ForeignKey('sales_hj."REQUESTS_HJ".request_id', ondelete="CASCADE"), nullable=False, index=True)
    old_status = Column(String(50), nullable=True)
    new_status = Column(String(50), nullable=False)
    changed_by = Column(String(255), nullable=True)
    changed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class SalesRequestHJ(Base):
    """
    SQLAlchemy ORM Model mapped to sales_hj.SALES_REQUESTS_HJ table.
    Full 19-column table mirroring the sales request lifecycle.
    """
    __tablename__ = "SALES_REQUESTS_HJ"
    __table_args__ = {"schema": "sales_hj"}

    request_id = Column(String(50), primary_key=True, index=True)
    customer_id = Column(String(255), nullable=True, index=True)
    email = Column(String(255), nullable=True)
    mobile = Column(String(50), nullable=True)
    status = Column(String(50), nullable=False, default="BOOKED", index=True)
    service = Column(String(100), nullable=False, default="AVIATION")
    passengers = Column(Integer, default=1)
    customer_details = Column(JSON, nullable=True, default=dict)
    service_details = Column(JSON, nullable=True, default=dict)
    event_flight_details = Column(JSON, nullable=True, default=dict)
    assigned_sales_rep_id = Column(Integer, nullable=True)
    assigned_sales_rep_name = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
