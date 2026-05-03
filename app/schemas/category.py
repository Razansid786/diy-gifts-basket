
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

class CategoryCreate(BaseModel):

    name: str = Field(..., max_length=100)
    slug: str = Field(..., max_length=120, description="URL-friendly identifier.")
    description: Optional[str] = Field("", max_length=500)
    image_url: Optional[str] = Field("", max_length=500)

class CategoryUpdate(BaseModel):

    name: Optional[str] = Field(None, max_length=100)
    slug: Optional[str] = Field(None, max_length=120)
    description: Optional[str] = Field(None, max_length=500)
    image_url: Optional[str] = Field(None, max_length=500)

class CategoryResponse(BaseModel):

    id: str
    name: str
    slug: str
    description: str
    image_url: str
    created_at: datetime

    model_config = {"from_attributes": True}