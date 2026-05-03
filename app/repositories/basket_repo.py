
from typing import List, Optional

from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from app.models.basket import Basket, BasketItem, GiftBase
from app.models.product import Product
from app.repositories.base import BaseRepository

class GiftBaseRepository(BaseRepository[GiftBase]):

    model = GiftBase

    def __init__(self, db: AsyncSession):
        super().__init__(db)

class BasketRepository(BaseRepository[Basket]):

    model = Basket

    def __init__(self, db: AsyncSession):
        super().__init__(db)

    async def get_with_items(self, basket_id: str) -> Optional[Basket]:

        result = await self.db.execute(
            select(Basket)
            .options(
                selectinload(Basket.items).joinedload(BasketItem.product),
                joinedload(Basket.base),
            )
            .where(Basket.id == basket_id)
        )
        return result.scalars().first()

    async def get_with_personalization(self, basket_id: str) -> Optional[Basket]:

        result = await self.db.execute(
            select(Basket)
            .options(
                joinedload(Basket.base),
                joinedload(Basket.personalization),
            )
            .where(Basket.id == basket_id)
        )
        return result.scalars().first()

    async def get_with_base(self, basket_id: str) -> Optional[Basket]:

        result = await self.db.execute(
            select(Basket)
            .options(joinedload(Basket.base))
            .where(Basket.id == basket_id)
        )
        return result.scalars().first()

    async def get_many_with_items(self, basket_ids: List[str]) -> List[Basket]:

        if not basket_ids:
            return []

        result = await self.db.execute(
            select(Basket)
            .options(
                selectinload(Basket.items).joinedload(BasketItem.product),
                joinedload(Basket.base),
                joinedload(Basket.personalization),
            )
            .where(Basket.id.in_(basket_ids))
        )
        return list(result.unique().scalars().all())

    async def get_totals_by_ids(self, basket_ids: List[str]) -> dict[str, float]:

        if not basket_ids:
            return {}

        item_totals_subq = (
            select(
                BasketItem.basket_id.label("basket_id"),
                func.coalesce(func.sum(Product.price * BasketItem.quantity), 0).label(
                    "items_total"
                ),
            )
            .select_from(BasketItem)
            .join(Product, Product.id == BasketItem.product_id)
            .where(BasketItem.basket_id.in_(basket_ids))
            .group_by(BasketItem.basket_id)
            .subquery()
        )

        result = await self.db.execute(
            select(
                Basket.id,
                (
                    func.coalesce(GiftBase.price, 0)
                    + func.coalesce(item_totals_subq.c.items_total, 0)
                ).label("basket_total"),
            )
            .select_from(Basket)
            .outerjoin(GiftBase, GiftBase.id == Basket.base_id)
            .outerjoin(item_totals_subq, item_totals_subq.c.basket_id == Basket.id)
            .where(Basket.id.in_(basket_ids))
        )

        return {
            basket_id: round(float(total or 0), 2)
            for basket_id, total in result.all()
        }

    async def get_total(self, basket_id: str) -> float:

        totals = await self.get_totals_by_ids([basket_id])
        return totals.get(basket_id, 0.0)

    async def get_user_baskets(
        self, user_id: str, status: Optional[str] = None
    ) -> List[Basket]:

        stmt = select(Basket).where(Basket.user_id == user_id)
        if status:
            stmt = stmt.where(Basket.status == status)
        stmt = stmt.order_by(Basket.created_at.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_guest_baskets(
        self, session_id: str, status: Optional[str] = None
    ) -> List[Basket]:

        stmt = select(Basket).where(Basket.session_id == session_id)
        if status:
            stmt = stmt.where(Basket.status == status)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

class BasketItemRepository(BaseRepository[BasketItem]):

    model = BasketItem

    def __init__(self, db: AsyncSession):
        super().__init__(db)

    async def get_items_for_basket(self, basket_id: str) -> List[BasketItem]:

        result = await self.db.execute(
            select(BasketItem).where(BasketItem.basket_id == basket_id)
        )
        return list(result.scalars().all())

    async def count_items_in_basket(self, basket_id: str) -> int:

        result = await self.db.execute(
            select(func.coalesce(func.sum(BasketItem.quantity), 0)).where(
                BasketItem.basket_id == basket_id
            )
        )
        return int(result.scalar() or 0)

    async def replace_items(self, basket_id: str, items_data: List[dict]) -> List[BasketItem]:

        await self.db.execute(
            delete(BasketItem).where(BasketItem.basket_id == basket_id)
        )

        new_items = [
            BasketItem(
                basket_id=basket_id,
                product_id=item["product_id"],
                quantity=item["quantity"],
            )
            for item in items_data
        ]
        self.db.add_all(new_items)
        await self.db.flush()

        return new_items