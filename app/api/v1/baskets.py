"""
app/api/v1/baskets.py
─────────────────────
Basket builder endpoints (FR11–FR17).

Routes:
    POST   /baskets                    — Create a new basket (FR11).
    PUT    /baskets/{id}/base          — Select/change the base (FR12).
    POST   /baskets/{id}/items         — Add an item (FR14, FR15).
    DELETE /baskets/{id}/items/{iid}   — Remove an item (FR16).
    GET    /baskets/{id}/summary       — Review basket summary (FR17).
    POST   /baskets/{id}/complete      — Mark basket as complete.
    GET    /baskets/bases              — List available containers.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user_optional
from app.db.session import get_db
from app.schemas.basket import (
    BasketCreate,
    BasketItemAdd,
    BasketResponse,
    BasketSetBase,
    GiftBaseResponse,
)
from app.services.basket_service import BasketService

router = APIRouter(prefix="/baskets", tags=["Basket Builder"])


@router.get(
    "/bases",
    response_model=List[GiftBaseResponse],
    summary="List available gift bases / containers (FR12)",
)
async def list_bases(db: AsyncSession = Depends(get_db)):
    """Return all base containers (Baskets, Boxes, Tins) with sizes and prices."""
    service = BasketService(db)
    return await service.list_bases()


@router.post(
    "/",
    response_model=BasketResponse,
    status_code=201,
    summary="Create a new basket (FR11)",
)
async def create_basket(
    data: BasketCreate,
    current_user=Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """
    Start a new basket build.

    Authenticated users are linked automatically; guests should
    provide a ``session_id`` in the request body.
    """
    user_id = current_user.id if current_user else None
    service = BasketService(db)
    basket = await service.create_basket(user_id=user_id, data=data)

    # Calculate running total for the response
    summary = await service.get_basket_summary(basket.id)
    return BasketResponse(
        id=basket.id,
        user_id=basket.user_id,
        session_id=basket.session_id,
        base=basket.base,
        status=basket.status,
        items=basket.items,
        running_total=summary["running_total"],
        created_at=basket.created_at,
    )


@router.put(
    "/{basket_id}/base",
    response_model=BasketResponse,
    summary="Select or change the base container (FR12)",
)
async def set_base(
    basket_id: str,
    data: BasketSetBase,
    db: AsyncSession = Depends(get_db),
):
    """Assign a gift base (container) to the basket."""
    service = BasketService(db)
    basket = await service.set_base(basket_id, data.base_id)
    summary = await service.get_basket_summary(basket.id)
    return BasketResponse(
        id=basket.id,
        user_id=basket.user_id,
        session_id=basket.session_id,
        base=basket.base,
        status=basket.status,
        items=basket.items,
        running_total=summary["running_total"],
        created_at=basket.created_at,
    )


@router.post(
    "/{basket_id}/items",
    response_model=BasketResponse,
    status_code=201,
    summary="Add an item to the basket (FR14, FR15)",
)
async def add_item(
    basket_id: str,
    data: BasketItemAdd,
    db: AsyncSession = Depends(get_db),
):
    """Add a product to the basket (enforces capacity limit)."""
    service = BasketService(db)
    basket = await service.add_item(basket_id, data)
    summary = await service.get_basket_summary(basket.id)
    return BasketResponse(
        id=basket.id,
        user_id=basket.user_id,
        session_id=basket.session_id,
        base=basket.base,
        status=basket.status,
        items=basket.items,
        running_total=summary["running_total"],
        created_at=basket.created_at,
    )


@router.delete(
    "/{basket_id}/items/{item_id}",
    response_model=BasketResponse,
    summary="Remove an item from the basket (FR16)",
)
async def remove_item(
    basket_id: str,
    item_id: str,
    db: AsyncSession = Depends(get_db),
):
    """One-click removal of an item from the basket."""
    service = BasketService(db)
    basket = await service.remove_item(basket_id, item_id)
    summary = await service.get_basket_summary(basket.id)
    return BasketResponse(
        id=basket.id,
        user_id=basket.user_id,
        session_id=basket.session_id,
        base=basket.base,
        status=basket.status,
        items=basket.items,
        running_total=summary["running_total"],
        created_at=basket.created_at,
    )


@router.get(
    "/{basket_id}/summary",
    response_model=BasketResponse,
    summary="Review basket summary (FR17)",
)
async def get_summary(
    basket_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Return the full basket summary including items and running total.

    Used for the 'Review My Basket' page before checkout.
    """
    service = BasketService(db)
    summary = await service.get_basket_summary(basket_id)
    basket = summary["basket"]
    return BasketResponse(
        id=basket.id,
        user_id=basket.user_id,
        session_id=basket.session_id,
        base=basket.base,
        status=basket.status,
        items=basket.items,
        running_total=summary["running_total"],
        created_at=basket.created_at,
    )


@router.post(
    "/{basket_id}/complete",
    response_model=BasketResponse,
    summary="Mark basket as complete",
)
async def complete_basket(
    basket_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Mark the basket as complete so it can be added to the cart."""
    service = BasketService(db)
    basket = await service.complete_basket(basket_id)
    summary = await service.get_basket_summary(basket.id)
    return BasketResponse(
        id=basket.id,
        user_id=basket.user_id,
        session_id=basket.session_id,
        base=basket.base,
        status=basket.status,
        items=basket.items,
        running_total=summary["running_total"],
        created_at=basket.created_at,
    )
