"""
app/schemas/basket.py
─────────────────────
Pydantic schemas for the basket builder wizard (FR11–FR17).
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


# ── Gift Base (container) schemas ────────────────────────────────────

class GiftBaseCreate(BaseModel):
    """Admin payload for adding a new container type."""
    name: str = Field(..., max_length=100)
    size: str = Field(..., description="S, M, or L.")
    price: float = Field(..., gt=0)
    image_url: Optional[str] = Field("", max_length=500)
    max_items: int = Field(..., gt=0, description="Capacity limit (FR14).")


class GiftBaseResponse(BaseModel):
    """Public representation of a gift base / container."""
    id: str
    name: str
    size: str
    price: float
    image_url: str
    max_items: int

    model_config = {"from_attributes": True}


# ── Basket item schemas ──────────────────────────────────────────────

class BasketItemAdd(BaseModel):
    """Payload for adding a product to a basket (FR15)."""
    product_id: str
    quantity: int = Field(1, ge=1)


class BasketItemResponse(BaseModel):
    """An item inside a basket."""
    id: str
    product_id: str
    quantity: int

    model_config = {"from_attributes": True}


# ── Basket schemas ───────────────────────────────────────────────────

class BasketCreate(BaseModel):
    """Start a new basket build (FR11).  Optionally select a base."""
    base_id: Optional[str] = Field(None, description="Container to use (FR12).")
    session_id: Optional[str] = Field(None, description="Guest session ID.")


class BasketSetBase(BaseModel):
    """Select or change the base container for a basket (FR12)."""
    base_id: str


class BasketResponse(BaseModel):
    """Full basket view including items and running total (FR13, FR15, FR17)."""
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
