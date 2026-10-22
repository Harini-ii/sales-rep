from pydantic import BaseModel, EmailStr, Field

class AccountUpdate(BaseModel):
    full_name: str = Field(..., min_length=1, description="Full name cannot be empty")
    email: EmailStr
    mobile: str = Field(..., min_length=1, description="Mobile number cannot be empty")

class PasswordUpdate(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8, description="Password must be at least 8 characters long")
    confirm_password: str
