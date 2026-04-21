"""
app/schemas/cart.py
───────────────────
Pydantic schemas for cart management (FR22).
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.basket import BasketResponse


class CartItemAdd(BaseModel):
    """Payload for adding a completed basket to the cart."""
    basket_id: str
    quantity: int = Field(1, ge=1)


class CartItemUpdate(BaseModel):
    """Payload for editing the quantity of a cart item (FR22)."""
    quantity: int = Field(..., ge=1)


class CartItemResponse(BaseModel):
    """A single cart line item."""
    id: str
    basket_id: str
    quantity: int

    model_config = {"from_attributes": True}


class CartResponse(BaseModel):
    """Full cart view with line items and computed totals."""
    id: str
    user_id: Optional[str]
    session_id: Optional[str]
    items: List[CartItemResponse] = []
    subtotal: float = Field(
        0, description="Sum of all basket totals × quantities.",
    )
    shipping_fee: float = Field(
        0, description="Flat-rate or order-based shipping (FR23).",
    )
    total: float = Field(0, description="subtotal + shipping_fee.")
    created_at: datetime

    model_config = {"from_attributes": True}
