
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

class AddressCreate(BaseModel):

    label: str = Field("Home", max_length=50, description="e.g. 'Home', 'Office'.")
    line1: str = Field(..., max_length=255)
    line2: Optional[str] = Field("", max_length=255)
    city: str = Field(..., max_length=100)
    state: str = Field(..., max_length=100)
    zip_code: str = Field(..., max_length=20)
    country: str = Field("US", max_length=100)
    is_default: bool = False

class AddressUpdate(BaseModel):

    label: Optional[str] = Field(None, max_length=50)
    line1: Optional[str] = Field(None, max_length=255)
    line2: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    zip_code: Optional[str] = Field(None, max_length=20)
    country: Optional[str] = Field(None, max_length=100)
    is_default: Optional[bool] = None

class AddressResponse(BaseModel):

    id: str
    user_id: str
    label: str
    line1: str
    line2: str
    city: str
    state: str
    zip_code: str
    country: str
    is_default: bool
    created_at: datetime

    model_config = {"from_attributes": True}