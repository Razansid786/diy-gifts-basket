
from typing import List, Optional

from fastapi import APIRouter, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user_optional
from app.db.session import get_db
from app.schemas.basket import (
    BasketCreate,
    BasketItemAdd,
    BasketItemsSync,
    BasketResponse,
    BasketSetBase,
    CompleteAndCartRequest,
    GiftBaseResponse,
    QuickBuyRequest,
)
from app.services.basket_service import BasketService

router = APIRouter(prefix="/baskets", tags=["Basket Builder"])

def _build_response(result: dict) -> BasketResponse:

    basket = result["basket"]
    return BasketResponse(
        id=basket.id,
        user_id=basket.user_id,
        session_id=basket.session_id,
        base=basket.base,
        status=basket.status,
        items=basket.items,
        running_total=result["running_total"],
        created_at=basket.created_at,
    )

@router.get(
    "/bases",
    response_model=List[GiftBaseResponse],
    summary="List available gift bases / containers (FR12)",
)
async def list_bases(db: AsyncSession = Depends(get_db)):

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

    user_id = current_user.id if current_user else None
    service = BasketService(db)
    result = await service.create_basket(user_id=user_id, data=data)
    return _build_response(result)

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

    service = BasketService(db)
    result = await service.set_base(basket_id, data.base_id)
    return _build_response(result)

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

    service = BasketService(db)
    result = await service.add_item(basket_id, data)
    return _build_response(result)

@router.put(
    "/{basket_id}/items/sync",
    response_model=BasketResponse,
    summary="Replace basket items in one request",
)
async def sync_items(
    basket_id: str,
    data: BasketItemsSync,
    db: AsyncSession = Depends(get_db),
):

    service = BasketService(db)
    result = await service.sync_items(basket_id, data)
    return _build_response(result)


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

    service = BasketService(db)
    result = await service.remove_item(basket_id, item_id)
    return _build_response(result)

@router.get(
    "/{basket_id}/summary",
    response_model=BasketResponse,
    summary="Review basket summary (FR17)",
)
async def get_summary(
    basket_id: str,
    db: AsyncSession = Depends(get_db),
):

    service = BasketService(db)
    result = await service.get_basket_summary(basket_id)
    return _build_response(result)

@router.post(
    "/{basket_id}/complete",
    response_model=BasketResponse,
    summary="Mark basket as complete",
)
async def complete_basket(
    basket_id: str,
    db: AsyncSession = Depends(get_db),
):

    service = BasketService(db)
    result = await service.complete_basket(basket_id)
    return _build_response(result)

@router.post(
    "/{basket_id}/complete-and-cart",
    response_model=BasketResponse,
    status_code=201,
    summary="Complete basket and add to cart in one call",
)
async def complete_and_add_to_cart(
    basket_id: str,
    data: CompleteAndCartRequest,
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID"),
    current_user=Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):

    user_id = current_user.id if current_user else None
    service = BasketService(db)
    result = await service.complete_and_add_to_cart(
        basket_id=basket_id,
        user_id=user_id,
        session_id=x_session_id,
        data=data,
    )
    return _build_response(result)

@router.post(
    "/quick-buy",
    response_model=BasketResponse,
    status_code=201,
    summary="Buy a prebuilt basket in one call",
)
async def quick_buy(
    data: QuickBuyRequest,
    current_user=Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):

    user_id = current_user.id if current_user else None
    service = BasketService(db)
    result = await service.quick_buy(user_id=user_id, data=data)
    return _build_response(result)