"""
app/schemas/user.py
───────────────────
Pydantic schemas for user registration, login, and profile responses.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


# ── Registration (FR1) ───────────────────────────────────────────────

class UserCreate(BaseModel):
    """Payload for creating a new user account."""
    email: EmailStr = Field(..., description="Unique email address.")
    password: str = Field(..., min_length=8, description="Plain-text password (≥ 8 chars).")
    full_name: str = Field("", max_length=150, description="Display name.")


# ── Login (FR2) ──────────────────────────────────────────────────────

class UserLogin(BaseModel):
    """Payload for email+password login."""
    email: EmailStr
    password: str


# ── Token response ───────────────────────────────────────────────────

class TokenResponse(BaseModel):
    """JWT token returned after successful login or registration."""
    access_token: str
    token_type: str = "bearer"


# ── Profile update ───────────────────────────────────────────────────

class UserUpdate(BaseModel):
    """Partial update for the user's own profile."""
    full_name: Optional[str] = Field(None, max_length=150)
    email: Optional[EmailStr] = None


# ── Response ─────────────────────────────────────────────────────────

class UserResponse(BaseModel):
    """Public representation of a user (never exposes the password hash)."""
    id: str
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
