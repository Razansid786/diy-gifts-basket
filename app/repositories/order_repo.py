"""
app/repositories/order_repo.py
──────────────────────────────
Data-access layer for the ``orders`` and ``order_items`` tables (FR23–FR30).
"""

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.order import Order, OrderItem
from app.repositories.base import BaseRepository


class OrderRepository(BaseRepository[Order]):
    """Repository for order queries and updates."""

    model = Order

    def __init__(self, db: AsyncSession):
        super().__init__(db)

    async def get_with_items(self, order_id: str) -> Optional[Order]:
        """Fetch an order with its line items eagerly loaded."""
        result = await self.db.execute(
            select(Order)
            .options(selectinload(Order.items))
            .where(Order.id == order_id)
        )
        return result.scalars().first()

    async def get_user_orders(self, user_id: str) -> List[Order]:
        """
        Return all orders for a user, newest first (FR3 — My Orders page).
        """
        result = await self.db.execute(
            select(Order)
            .options(selectinload(Order.items))
            .where(Order.user_id == user_id)
            .order_by(Order.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_all_sorted(
        self, skip: int = 0, limit: int = 50
    ) -> List[Order]:
        """
        Return all orders sorted by date, newest first (FR28 — Admin view).
        """
        result = await self.db.execute(
            select(Order)
            .options(selectinload(Order.items))
            .order_by(Order.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_payment_ref(self, payment_ref: str) -> Optional[Order]:
        """
        Look up an order by its payment reference.

        Used for idempotency checks to prevent duplicate orders (NFR4).
        """
        result = await self.db.execute(
            select(Order).where(Order.payment_ref == payment_ref)
        )
        return result.scalars().first()


class OrderItemRepository(BaseRepository[OrderItem]):
    """Repository for order line items."""

    model = OrderItem

    def __init__(self, db: AsyncSession):
        super().__init__(db)
