
from typing import Optional

from fastapi import APIRouter, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user_optional
from app.db.session import get_db
from app.schemas.cart import CartItemAdd, CartItemUpdate, CartResponse
from app.services.cart_service import CartService

router = APIRouter(prefix="/cart", tags=["Cart"])

def _get_ids(current_user, session_id: Optional[str]):

    user_id = current_user.id if current_user else None
    return user_id, session_id

@router.get(
    "/",
    response_model=CartResponse,
    summary="Get the current cart with calculated totals",
)
async def get_cart(
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID"),
    current_user=Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):

    user_id, session_id = _get_ids(current_user, x_session_id)
    service = CartService(db)
    result = await service.get_cart(user_id=user_id, session_id=session_id)

    cart = result["cart"]
    return CartResponse(
        id=cart.id,
        user_id=cart.user_id,
        session_id=cart.session_id,
        items=cart.items,
        subtotal=result["subtotal"],
        shipping_fee=result["shipping_fee"],
        total=result["total"],
        created_at=cart.created_at,
    )

@router.post(
    "/items",
    response_model=CartResponse,
    status_code=201,
    summary="Add a completed basket to the cart",
)
async def add_to_cart(
    data: CartItemAdd,
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID"),
    current_user=Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):

    user_id, session_id = _get_ids(current_user, x_session_id)
    service = CartService(db)
    result = await service.add_item(
        data=data, user_id=user_id, session_id=session_id
    )

    cart = result["cart"]
    return CartResponse(
        id=cart.id,
        user_id=cart.user_id,
        session_id=cart.session_id,
        items=cart.items,
        subtotal=result["subtotal"],
        shipping_fee=result["shipping_fee"],
        total=result["total"],
        created_at=cart.created_at,
    )

@router.put(
    "/items/{item_id}",
    response_model=CartResponse,
    summary="Edit cart item quantity (FR22)",
)
async def update_cart_item(
    item_id: str,
    data: CartItemUpdate,
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID"),
    current_user=Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):

    user_id, session_id = _get_ids(current_user, x_session_id)
    service = CartService(db)
    result = await service.update_item(
        item_id=item_id, data=data, user_id=user_id, session_id=session_id
    )

    cart = result["cart"]
    return CartResponse(
        id=cart.id,
        user_id=cart.user_id,
        session_id=cart.session_id,
        items=cart.items,
        subtotal=result["subtotal"],
        shipping_fee=result["shipping_fee"],
        total=result["total"],
        created_at=cart.created_at,
    )

@router.delete(
    "/items/{item_id}",
    response_model=CartResponse,
    summary="Remove a cart item",
)
async def remove_cart_item(
    item_id: str,
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID"),
    current_user=Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):

    user_id, session_id = _get_ids(current_user, x_session_id)
    service = CartService(db)
    result = await service.remove_item(
        item_id=item_id, user_id=user_id, session_id=session_id
    )

    cart = result["cart"]
    return CartResponse(
        id=cart.id,
        user_id=cart.user_id,
        session_id=cart.session_id,
        items=cart.items,
        subtotal=result["subtotal"],
        shipping_fee=result["shipping_fee"],
        total=result["total"],
        created_at=cart.created_at,
    )