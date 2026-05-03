
from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, Field

class GiftBaseCreate(BaseModel):

    name: str = Field(..., max_length=100)
    size: str = Field(..., description="S, M, or L.")
    price: float = Field(..., gt=0)
    image_url: Optional[str] = Field("", max_length=500)
    max_items: int = Field(..., gt=0, description="Capacity limit (FR14).")

class GiftBaseResponse(BaseModel):

    id: str
    name: str
    size: str
    price: float
    image_url: str
    max_items: int

    model_config = {"from_attributes": True}

class BasketItemAdd(BaseModel):

    product_id: str
    quantity: int = Field(1, ge=1)

class BasketItemSync(BaseModel):

    product_id: str
    quantity: int = Field(1, ge=1)

class BasketItemsSync(BaseModel):

    items: List[BasketItemSync] = Field(default_factory=list, min_length=1)

class BasketItemResponse(BaseModel):

    id: str
    product_id: str
    quantity: int

    model_config = {"from_attributes": True}

class BasketCreate(BaseModel):

    base_id: Optional[str] = Field(None, description="Container to use (FR12).")
    session_id: Optional[str] = Field(None, description="Guest session ID.")

class BasketSetBase(BaseModel):

    base_id: str

class BasketResponse(BaseModel):

    id: str
    user_id: Optional[str]
    session_id: Optional[str]
    base: Optional[GiftBaseResponse]
    status: str
    items: List[BasketItemResponse] = []
    running_total: float = Field(
        0, description="Dynamic price: base + sum(item prices × quantities) (FR13).",
    )
    created_at: datetime

    model_config = {"from_attributes": True}

class QuickBuyItemPayload(BaseModel):

    product_id: str
    quantity: int = Field(1, ge=1)

class PersonalizationPayload(BaseModel):

    gift_message: Optional[str] = None
    ribbon_color: Optional[str] = None
    requested_delivery_date: Optional[date] = None

class QuickBuyRequest(BaseModel):

    base_id: str
    session_id: Optional[str] = None
    items: List[QuickBuyItemPayload] = Field(..., min_length=1)
    personalization: Optional[PersonalizationPayload] = None

class CompleteAndCartRequest(BaseModel):

    personalization: Optional[PersonalizationPayload] = None