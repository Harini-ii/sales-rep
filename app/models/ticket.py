import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class SupportTicket(Base):
    """
    SQLAlchemy ORM Model mapped to sales_hj.SUPPORT_TICKETS_LEGACY_HJ table.
    Preserved for backwards-compatibility.
    """
    __tablename__ = "SUPPORT_TICKETS_LEGACY_HJ"
    __table_args__ = {"schema": "sales_hj"}

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(String(255), nullable=False, index=True)
    customer_name = Column(String(255), nullable=True)
    subject = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    status = Column(String(50), nullable=False, default="OPEN")
    reply = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class SupportTicketHJ(Base):
    """
    SQLAlchemy ORM Model mapped to sales_hj.SUPPORT_TICKETS_HJ table.
    Uses UUID for primary key and tracks request_id, request_role, status, and admin_response.
    """
    __tablename__ = "SUPPORT_TICKETS_HJ"
    __table_args__ = {"schema": "sales_hj"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    requester_id = Column(String(50), default=lambda: str(uuid.uuid4()), nullable=True, index=True)
    requester_role = Column(String(50), nullable=True, default="SALES")

    @property
    def request_id(self) -> str | None:
        return self.requester_id

    @request_id.setter
    def request_id(self, val: str):
        self.requester_id = val

    @property
    def request_role(self) -> str | None:
        return self.requester_role

    @request_role.setter
    def request_role(self, val: str):
        self.requester_role = val
    subject = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    status = Column(String(50), nullable=False, default="OPEN", index=True)
    admin_response = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
