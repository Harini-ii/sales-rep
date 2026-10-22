import uuid
from datetime import date, datetime, timezone
from sqlalchemy import Column, Integer, String, Date, DateTime
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class CustomerModel(Base):
    """
    SQLAlchemy ORM Model mapped to sales_hj.CUSTOMERS_HJ table.
    Stores customer records in the sales schema, automatically synchronized
    with customer_hj.CUSTOMER_PROFILE via database trigger.
    """
    __tablename__ = "CUSTOMERS_HJ"
    __table_args__ = {"schema": "sales_hj"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    customer_id = Column(UUID(as_uuid=True), unique=True, default=uuid.uuid4, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    mobile = Column(String(50), nullable=True)
    subscription = Column(String(100), default="Basic")
    credits = Column(Integer, default=0)
    purchases = Column(Integer, default=0)
    country = Column(String(100), default="")
    company = Column(String(255), default="")
    joined = Column(Date, default=date.today)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
