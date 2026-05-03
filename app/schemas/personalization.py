
from datetime import date
from typing import Optional

from pydantic import BaseModel, Field

class PersonalizationUpdate(BaseModel):

    gift_message: Optional[str] = Field(
        None, max_length=250,
        description="Custom note (max 250 chars — FR18).",
    )
    ribbon_color: Optional[str] = Field(
        None, max_length=30,
        description="Chosen ribbon color from predefined list (FR19).",
    )
    requested_delivery_date: Optional[date] = Field(
        None, description="Preferred delivery date (FR21).",
    )

class PersonalizationResponse(BaseModel):

    id: str
    basket_id: str
    gift_message: Optional[str]
    ribbon_color: Optional[str]
    gift_tag_image_url: Optional[str]
    requested_delivery_date: Optional[date]

    model_config = {"from_attributes": True}