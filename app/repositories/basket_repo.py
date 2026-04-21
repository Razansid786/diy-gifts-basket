"""
app/repositories/basket_repo.py
───────────────────────────────
Data-access layer for the basket builder tables (FR11–FR17).
"""

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.basket import Basket, BasketItem, GiftBase
from app.repositories.base import BaseRepository


class GiftBaseRepository(BaseRepository[GiftBase]):
    """Repository for gift base / container CRUD."""

    model = GiftBase

    def __init__(self, db: AsyncSession):
        super().__init__(db)


class BasketRepository(BaseRepository[Basket]):
    """Repository for basket CRUD and item management."""

    model = Basket

    def __init__(self, db: AsyncSession):
        super().__init__(db)

    async def get_with_items(self, basket_id: str) -> Optional[Basket]:
        """
        Fetch a basket with its items and base eagerly loaded.

        This avoids N+1 queries when computing the running total (FR13)
        or rendering the 'Current Contents' view (FR15).
        """
        result = await self.db.execute(
            select(Basket)
            .options(
                selectinload(Basket.items),
                selectinload(Basket.base),
                selectinload(Basket.personalization),
            )
            .where(Basket.id == basket_id)
        )
        return result.scalars().first()

    async def get_user_baskets(
        self, user_id: str, status: Optional[str] = None
    ) -> List[Basket]:
        """Return all baskets for a registered user, optionally filtered by status."""
        stmt = select(Basket).where(Basket.user_id == user_id)
        if status:
            stmt = stmt.where(Basket.status == status)
        stmt = stmt.order_by(Basket.created_at.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_guest_baskets(
        self, session_id: str, status: Optional[str] = None
    ) -> List[Basket]:
        """Return all baskets for a guest session."""
        stmt = select(Basket).where(Basket.session_id == session_id)
        if status:
            stmt = stmt.where(Basket.status == status)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())


class BasketItemRepository(BaseRepository[BasketItem]):
    """Repository for individual items within a basket."""

    model = BasketItem

    def __init__(self, db: AsyncSession):
        super().__init__(db)

    async def get_items_for_basket(self, basket_id: str) -> List[BasketItem]:
        """Return all items in a specific basket (FR15)."""
        result = await self.db.execute(
            select(BasketItem).where(BasketItem.basket_id == basket_id)
        )
        return list(result.scalars().all())

    async def count_items_in_basket(self, basket_id: str) -> int:
        """
        Return the total number of individual items in a basket.

        Used to enforce the ``max_items`` capacity limit (FR14).
        Each item's quantity is summed.
        """
        items = await self.get_items_for_basket(basket_id)
        return sum(item.quantity for item in items)
