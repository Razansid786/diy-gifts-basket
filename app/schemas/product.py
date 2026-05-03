
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

class ProductCreate(BaseModel):

    sku: str = Field(..., max_length=50, description="Unique Stock Keeping Unit.")
    title: str = Field(..., max_length=200)
    description: Optional[str] = Field("", max_length=1000)
    price: float = Field(..., gt=0, description="Price in USD.")
    image_url: Optional[str] = Field("", max_length=500)
    category_id: Optional[str] = Field(None, description="FK to a category.")
    inventory_count: int = Field(0, ge=0)
    is_active: bool = True

class ProductUpdate(BaseModel):

    sku: Optional[str] = Field(None, max_length=50)
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    price: Optional[float] = Field(None, gt=0)
    image_url: Optional[str] = Field(None, max_length=500)
    category_id: Optional[str] = None
    inventory_count: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None

class ProductResponse(BaseModel):

    id: str
    sku: str
    title: str
    description: str
    price: float
    image_url: str
    category_id: Optional[str]
    inventory_count: int
    is_active: bool
    is_sold_out: bool = Field(
        ..., description="Computed: True when inventory_count == 0 (FR10).",
    )
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

class ProductSearchParams(BaseModel):

    q: Optional[str] = Field(None, description="Keyword search term.")
    category_id: Optional[str] = Field(None, description="Filter by category.")
    min_price: Optional[float] = Field(None, ge=0)
    max_price: Optional[float] = Field(None, ge=0)
    in_stock_only: bool = Field(False, description="Exclude sold-out items.")