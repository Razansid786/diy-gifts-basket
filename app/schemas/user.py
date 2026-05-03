
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field

class UserCreate(BaseModel):

    email: EmailStr = Field(..., description="Unique email address.")
    password: str = Field(..., min_length=8, description="Plain-text password (≥ 8 chars).")
    full_name: str = Field("", max_length=150, description="Display name.")
    phone_number: Optional[str] = Field(None, max_length=50, description="Contact phone number.")

class UserLogin(BaseModel):

    email: EmailStr
    password: str

class TokenResponse(BaseModel):

    access_token: str
    token_type: str = "bearer"

class UserUpdate(BaseModel):

    full_name: Optional[str] = Field(None, max_length=150)
    email: Optional[EmailStr] = None

class UserResponse(BaseModel):

    id: str
    email: str
    full_name: str
    phone_number: Optional[str]
    role: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}

class ForgotPasswordRequest(BaseModel):

    email: EmailStr

class ResetPasswordRequest(BaseModel):

    token: str = Field(..., description="The JWT reset token sent via email.")
    new_password: str = Field(..., min_length=8, description="The new password.")