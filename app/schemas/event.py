from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class SalesEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    event_id: UUID
    customer_id: Optional[UUID] = None
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = "pending"
    created_at: Optional[datetime] = None

    event_type: Optional[str] = None
    timing: Optional[str] = None
    event_details: Optional[str] = None
    event_date: Optional[str] = None
    event_time: Optional[str] = None
    number_of_people: Optional[int] = None
    aircraft_type: Optional[str] = None
    aircraft_model: Optional[str] = None

    food_preferences: Optional[str] = None
    drinks: Optional[str] = None
    champagne_service: Optional[bool] = False
    crew_preferences: Optional[str] = None

    full_name: Optional[str] = None
    email: Optional[str] = None
    mobile_number: Optional[str] = None
    identity_document: Optional[str] = None

    event_purpose: Optional[str] = None
    occasion_name: Optional[str] = None
    selected_experience: Optional[str] = None
    event_end_date: Optional[str] = None
    event_end_time: Optional[str] = None
    city_or_departure_area: Optional[str] = None
    venue: Optional[str] = None
    venue_address: Optional[str] = None
    estimated_budget: Optional[Decimal] = None
    budget_currency: Optional[str] = "USD"
    date_flexibility: Optional[str] = None
    event_notes: Optional[str] = None

    aircraft_passengers: Optional[int] = None
    flight_type: Optional[str] = None
    departure_location: Optional[str] = None
    event_destination: Optional[str] = None
    preferred_flight_date: Optional[str] = None
    preferred_departure_time: Optional[str] = None

    ground_pickup: Optional[bool] = False
    vehicle_transfer: Optional[bool] = False
    vip_reception: Optional[bool] = False
    baggage_coordination: Optional[bool] = False
    accessibility_assistance: Optional[bool] = False
    special_aviation_requirements: Optional[str] = None

    catering_requested: Optional[bool] = False
    dietary_preferences: Optional[str] = None
    meal_preferences: Optional[str] = None
    catering_notes: Optional[str] = None
    beverage_service_requested: Optional[bool] = False
    beverage_preferences: Optional[str] = None

    decorations_requested: Optional[bool] = False
    occasion_theme: Optional[str] = None
    decoration_notes: Optional[str] = None
    photography_videography_requested: Optional[bool] = False
    photography_notes: Optional[str] = None
    vip_guest_arrangements: Optional[str] = None
    privacy_requirements: Optional[str] = None
    special_assistance: Optional[str] = None
    other_experience_requirements: Optional[str] = None

    country: Optional[str] = None
    company: Optional[str] = None
    event_coordinator: Optional[str] = None
    alternate_contact_number: Optional[str] = None
    preferred_contact_method: Optional[str] = None
    contact_notes: Optional[str] = None
    terms_acknowledged: Optional[bool] = False


class SalesEventStatusUpdate(BaseModel):
    status: str


class SalesEventCreate(BaseModel):
    customer_id: Optional[UUID] = None
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = "pending"
    event_type: Optional[str] = None
    timing: Optional[str] = None
    event_details: Optional[str] = None
    event_date: Optional[str] = None
    event_time: Optional[str] = None
    number_of_people: Optional[int] = 1
    aircraft_type: Optional[str] = None
    aircraft_model: Optional[str] = None
    full_name: Optional[str] = None
    email: Optional[str] = None
    mobile_number: Optional[str] = None
    city_or_departure_area: Optional[str] = None
    venue: Optional[str] = None
    venue_address: Optional[str] = None
    estimated_budget: Optional[Decimal] = None
    budget_currency: Optional[str] = "USD"
    departure_location: Optional[str] = None
    event_destination: Optional[str] = None
    preferred_flight_date: Optional[str] = None
    preferred_departure_time: Optional[str] = None
    terms_acknowledged: Optional[bool] = False


class SalesEventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    event_type: Optional[str] = None
    timing: Optional[str] = None
    event_details: Optional[str] = None
    event_date: Optional[str] = None
    event_time: Optional[str] = None
    number_of_people: Optional[int] = None
    aircraft_type: Optional[str] = None
    aircraft_model: Optional[str] = None
    full_name: Optional[str] = None
    email: Optional[str] = None
    mobile_number: Optional[str] = None
    city_or_departure_area: Optional[str] = None
    venue: Optional[str] = None
    venue_address: Optional[str] = None
    estimated_budget: Optional[Decimal] = None
    budget_currency: Optional[str] = None
    departure_location: Optional[str] = None
    event_destination: Optional[str] = None
    preferred_flight_date: Optional[str] = None
    preferred_departure_time: Optional[str] = None
