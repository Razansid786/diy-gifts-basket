
from typing import List, Optional

from fastapi import APIRouter, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user, get_current_user_optional
from app.db.session import get_db
from app.schemas.order import CheckoutRequest, OrderResponse
from app.services.order_service import OrderService

router = APIRouter(prefix="/orders", tags=["Orders"])

@router.post(
    "/checkout",
    response_model=OrderResponse,
    status_code=201,
    summary="Place an order (FR25)",
)
async def checkout(
    data: CheckoutRequest,
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID"),
    current_user=Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):

    user_id = current_user.id if current_user else None
    service = OrderService(db)
    return await service.checkout(
        data=data,
        user_id=user_id,
        session_id=x_session_id,
    )

@router.get(
    "/",
    response_model=List[OrderResponse],
    summary="List my orders (FR3)",
)
async def list_my_orders(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):

    service = OrderService(db)
    return await service.get_user_orders(current_user.id)

@router.get(
    "/{order_id}",
    response_model=OrderResponse,
    summary="Get a single order",
)
async def get_order(
    order_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):

    service = OrderService(db)
    return await service.get_order(order_id)