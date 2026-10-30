import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Numeric
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
    status = Column(String(50), nullable=True, default="pending", index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    event_type = Column(String(100), nullable=True)
    timing = Column(String(100), nullable=True)
    event_details = Column(Text, nullable=True)
    event_date = Column(String(100), nullable=True)
    event_time = Column(String(100), nullable=True)
    number_of_people = Column(Integer, nullable=True)
    aircraft_type = Column(String(150), nullable=True)
    aircraft_model = Column(String(150), nullable=True)

    food_preferences = Column(Text, nullable=True)
    drinks = Column(Text, nullable=True)
    champagne_service = Column(Boolean, nullable=True, default=False)
    crew_preferences = Column(Text, nullable=True)

    full_name = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True, index=True)
    mobile_number = Column(String(50), nullable=True)
    identity_document = Column(Text, nullable=True)

    event_purpose = Column(String(255), nullable=True)
    occasion_name = Column(String(255), nullable=True)
    selected_experience = Column(String(255), nullable=True)
    event_end_date = Column(String(100), nullable=True)
    event_end_time = Column(String(100), nullable=True)
    city_or_departure_area = Column(String(255), nullable=True)
    venue = Column(String(255), nullable=True)
    venue_address = Column(Text, nullable=True)
    estimated_budget = Column(Numeric, nullable=True)
    budget_currency = Column(String(10), nullable=True, default="USD")
    date_flexibility = Column(String(100), nullable=True)
    event_notes = Column(Text, nullable=True)

    aircraft_passengers = Column(Integer, nullable=True)
    flight_type = Column(String(100), nullable=True)
    departure_location = Column(String(255), nullable=True)
    event_destination = Column(String(255), nullable=True)
    preferred_flight_date = Column(String(100), nullable=True)
    preferred_departure_time = Column(String(100), nullable=True)

    ground_pickup = Column(Boolean, nullable=True, default=False)
    vehicle_transfer = Column(Boolean, nullable=True, default=False)
    vip_reception = Column(Boolean, nullable=True, default=False)
    baggage_coordination = Column(Boolean, nullable=True, default=False)
    accessibility_assistance = Column(Boolean, nullable=True, default=False)
    special_aviation_requirements = Column(Text, nullable=True)

    catering_requested = Column(Boolean, nullable=True, default=False)
    dietary_preferences = Column(Text, nullable=True)
    meal_preferences = Column(Text, nullable=True)
    catering_notes = Column(Text, nullable=True)
    beverage_service_requested = Column(Boolean, nullable=True, default=False)
    beverage_preferences = Column(Text, nullable=True)

    decorations_requested = Column(Boolean, nullable=True, default=False)
    occasion_theme = Column(String(255), nullable=True)
    decoration_notes = Column(Text, nullable=True)
    photography_videography_requested = Column(Boolean, nullable=True, default=False)
    photography_notes = Column(Text, nullable=True)
    vip_guest_arrangements = Column(Text, nullable=True)
    privacy_requirements = Column(Text, nullable=True)
    special_assistance = Column(Text, nullable=True)
    other_experience_requirements = Column(Text, nullable=True)

    country = Column(String(100), nullable=True)
    company = Column(String(255), nullable=True)
    event_coordinator = Column(String(255), nullable=True)
    alternate_contact_number = Column(String(50), nullable=True)
    preferred_contact_method = Column(String(50), nullable=True)
    contact_notes = Column(Text, nullable=True)
    terms_acknowledged = Column(Boolean, nullable=False, default=False)
