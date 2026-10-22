from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class AircraftImage(Base):
    """
    SQLAlchemy ORM Model mapped to sales_hj.aircraft_images table.
    Stores aircraft image metadata, public URLs, and catalogue indexing.
    """
    __tablename__ = "AIRCRAFT_IMAGES_HJ"
    __table_args__ = {"schema": "sales_hj"}

    # id = Column(Integer, primary_key=True, index=True)  # Redundant surrogate key; image_id (UUID) is primary key
    image_id = Column(UUID(as_uuid=True), primary_key=True, nullable=False, index=True)
    image_name = Column(String(255), nullable=False, index=True)
    image_url = Column(Text, nullable=False)
    category = Column(String(50), nullable=True, index=True)
    aircraft_model = Column(String(150), nullable=True, index=True)
    file_format = Column(String(10), nullable=True)
    # r2_key = Column(Text, unique=True, nullable=True)  # Not required; image_url contains full CDN path
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    is_active = Column(Boolean, default=True)
