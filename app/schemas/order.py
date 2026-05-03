
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field

class ShippingInfo(BaseModel):

    line1: str = Field(..., max_length=255)
    line2: Optional[str] = Field("", max_length=255)
    city: str = Field(..., max_length=100)
    state: str = Field(..., max_length=100)
    zip_code: str = Field(..., max_length=20)
    country: str = Field("US", max_length=100)

class CheckoutRequest(BaseModel):

    shipping: ShippingInfo
    guest_email: Optional[EmailStr] = Field(
        None, description="Required for guest checkout (FR5).",
    )
    address_id: Optional[str] = Field(
        None, description="Use a saved address instead of inline shipping.",
    )

class OrderStatusUpdate(BaseModel):

    status: str = Field(
        ..., description="New status: 'processing', 'shipped', or 'delivered'.",
    )

class OrderItemResponse(BaseModel):

    id: str
    basket_id: Optional[str]
    unit_price: float
    quantity: int

    model_config = {"from_attributes": True}

class OrderResponse(BaseModel):

    id: str
    user_id: Optional[str]
    guest_email: Optional[str]
    shipping_address_json: str
    shipping_fee: float
    subtotal: float
    total: float
    status: str
    payment_ref: Optional[str]
    items: List[OrderItemResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

class PackingListItem(BaseModel):

    product_id: str
    product_title: str
    product_sku: str
    quantity: int

class PackingListResponse(BaseModel):

    order_id: str
    basket_id: str
    base_name: str
    base_size: str
    items: List[PackingListItem] = []
    personalization_message: Optional[str]
    ribbon_color: Optional[str]
    gift_tag_image_url: Optional[str]
    requested_delivery_date: Optional[str]