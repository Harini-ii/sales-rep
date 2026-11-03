from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import date, datetime
from typing import Optional, Any


from pydantic import BaseModel, EmailStr, ConfigDict, model_validator
from datetime import date, datetime
from typing import Optional, Any


class CustomerEntitlement(BaseModel):
    subscription_status: Optional[str] = "ACTIVE"
    subscription_plan: Optional[str] = "Basic"
    credits_remaining: Optional[int] = 0

    model_config = ConfigDict(from_attributes=True)


class CustomerBase(BaseModel):
    full_name: Optional[str] = None
    name: Optional[str] = None
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
    entitlement: Optional[CustomerEntitlement] = None

    @model_validator(mode="before")
    @classmethod
    def sync_name_fields(cls, data: Any):
        if isinstance(data, dict):
            fn = data.get("full_name") or data.get("name")
            data["full_name"] = fn
            data["name"] = fn
        return data

    @model_validator(mode="after")
    def populate_defaults_and_entitlement(self):
        if not self.full_name and self.name:
            self.full_name = self.name
        elif not self.name and self.full_name:
            self.name = self.full_name

        if self.entitlement is None:
            self.entitlement = CustomerEntitlement(
                subscription_status="ACTIVE" if (self.subscription and self.subscription.lower() != "none") else "INACTIVE",
                subscription_plan=self.subscription or "Basic",
                credits_remaining=self.credits or 0,
            )
        return self


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



