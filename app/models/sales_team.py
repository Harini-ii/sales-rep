import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class SalesTeamMember(Base):
    """
    SQLAlchemy ORM Model mapped to admin_hj.SALES_TEAM_HJ table.
    Accesses and manages the salesperson's central account created by the Admin Dashboard.
    """
    __tablename__ = "SALES_TEAM_HJ"
    __table_args__ = {"schema": "admin_hj"}

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    mobile_number = Column(String(50), nullable=False)
    department = Column(String(100), nullable=False, default="sales")
    notes = Column(String, nullable=True)
    identity_document = Column(String, nullable=True)
    joined_at = Column(DateTime, default=datetime.utcnow)


class PasswordChange(Base):
    """
    SQLAlchemy ORM Model mapped to sales_hj.PASSWORD_CHANGES_HJ table.
    Logs each password update event for audit and verification.
    """
    __tablename__ = "PASSWORD_CHANGES_HJ"
    __table_args__ = {"schema": "sales_hj"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    sales_team_id = Column(Integer, nullable=True)
    email = Column(String(255), nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    changed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class PersonalInformation(Base):
    """
    SQLAlchemy ORM Model mapped to sales_hj.PERSONAL_INFORMATION_HJ table.
    Stores and persists personal information changes for sales team members.
    """
    __tablename__ = "PERSONAL_INFORMATION_HJ"
    __table_args__ = {"schema": "sales_hj"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    sales_team_id = Column(Integer, nullable=True)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, index=True)
    mobile_number = Column(String(50), nullable=False)
    department = Column(String(100), nullable=True, default="Sales")
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
