from typing import Optional, Any
from pydantic import BaseModel, EmailStr, Field, model_validator


class AccountUpdate(BaseModel):
    full_name: str = Field(..., min_length=1, description="Full name cannot be empty")
    email: Optional[EmailStr] = None
    mobile: str = Field(..., min_length=1, description="Mobile number cannot be empty")


class PasswordUpdate(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8, description="Password must be at least 8 characters long")
    confirm_password: str

    @model_validator(mode="before")
    @classmethod
    def accept_camel_case(cls, data: Any):
        if isinstance(data, dict):
            if "currentPassword" in data and "current_password" not in data:
                data["current_password"] = data["currentPassword"]
            if "newPassword" in data and "new_password" not in data:
                data["new_password"] = data["newPassword"]
            if "confirmPassword" in data and "confirm_password" not in data:
                data["confirm_password"] = data["confirmPassword"]
        return data
