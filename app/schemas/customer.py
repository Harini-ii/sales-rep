from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import date, datetime
from typing import Optional, Any


class CustomerBase(BaseModel):
    name: str
    email: EmailStr
    mobile: Optional[str] = ""
    phone_number: Optional[str] = None
    subscription: Optional[str] = "Basic"
    credits: Optional[int] = 0
    purchases: Optional[int] = 0
    country: Optional[str] = ""
    company: Optional[str] = ""
    role: Optional[str] = "CUSTOMER"
    profile_url: Optional[str] = None
    joined: Optional[date] = None
    created_at: Optional[datetime] = None


class CustomerCreate(CustomerBase):
    pass


class Customer(CustomerBase):
    # Existing database rows may contain legacy values that are not valid
    # email addresses. Keep strict EmailStr validation for input, while allowing
    # the read API to return those stored values without failing serialization.
    email: str
    customer_id: str
    id: Optional[Any] = None  # Backwards-compatible alias for customer_id

    model_config = ConfigDict(from_attributes=True)



