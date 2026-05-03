
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.order import Order, OrderItem
from app.repositories.base import BaseRepository

class OrderRepository(BaseRepository[Order]):

    model = Order

    def __init__(self, db: AsyncSession):
        super().__init__(db)

    async def get_with_items(self, order_id: str) -> Optional[Order]:

        result = await self.db.execute(
            select(Order)
            .options(selectinload(Order.items))
            .where(Order.id == order_id)
        )
        return result.scalars().first()

    async def get_user_orders(self, user_id: str) -> List[Order]:

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

        result = await self.db.execute(
            select(Order)
            .options(selectinload(Order.items))
            .order_by(Order.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_payment_ref(self, payment_ref: str) -> Optional[Order]:

        result = await self.db.execute(
            select(Order).where(Order.payment_ref == payment_ref)
        )
        return result.scalars().first()

class OrderItemRepository(BaseRepository[OrderItem]):

    model = OrderItem

    def __init__(self, db: AsyncSession):
        super().__init__(db)

    async def create_many(self, items_data: List[dict]) -> List[OrderItem]:

        if not items_data:
            return []

        items = [OrderItem(**payload) for payload in items_data]
        self.db.add_all(items)
        await self.db.flush()
        return items