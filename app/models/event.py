import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class SalesEventHJ(Base):
    """
    SQLAlchemy ORM Model mapped to sales_hj.SALES_EVENTS_HJ table.
    Mirrors customer events from customer_hj.CUSTOMER_EVENTS (68 columns).
    """
    __tablename__ = "SALES_EVENTS_HJ"
    __table_args__ = {"schema": "sales_hj"}

    event_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    customer_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    title = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    status = Column(String(50), nullable=True, default="PENDING")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
