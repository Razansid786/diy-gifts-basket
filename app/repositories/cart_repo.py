
from typing import Optional

from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.orm.attributes import set_committed_value

from app.models.basket import Basket, BasketItem, GiftBase
from app.models.cart import Cart, CartItem
from app.models.product import Product
from app.repositories.base import BaseRepository

class CartRepository(BaseRepository[Cart]):

    model = Cart

    def __init__(self, db: AsyncSession):
        super().__init__(db)

    async def get_by_user(self, user_id: str) -> Optional[Cart]:

        result = await self.db.execute(
            select(Cart)
            .options(selectinload(Cart.items))
            .where(Cart.user_id == user_id)
        )
        return result.scalars().first()

    async def get_by_session(self, session_id: str) -> Optional[Cart]:

        result = await self.db.execute(
            select(Cart)
            .options(selectinload(Cart.items))
            .where(Cart.session_id == session_id)
        )
        return result.scalars().first()

    async def calculate_subtotal(self, cart_id: str) -> float:

        basket_item_totals_subq = (
            select(
                BasketItem.basket_id.label("basket_id"),
                func.coalesce(func.sum(Product.price * BasketItem.quantity), 0).label(
                    "items_total"
                ),
            )
            .select_from(BasketItem)
            .join(Product, Product.id == BasketItem.product_id)
            .group_by(BasketItem.basket_id)
            .subquery()
        )

        basket_totals_subq = (
            select(
                Basket.id.label("basket_id"),
                (
                    func.coalesce(GiftBase.price, 0)
                    + func.coalesce(basket_item_totals_subq.c.items_total, 0)
                ).label("basket_total"),
            )
            .select_from(Basket)
            .outerjoin(GiftBase, GiftBase.id == Basket.base_id)
            .outerjoin(
                basket_item_totals_subq,
                basket_item_totals_subq.c.basket_id == Basket.id,
            )
            .subquery()
        )

        result = await self.db.execute(
            select(
                func.coalesce(
                    func.sum(
                        CartItem.quantity
                        * func.coalesce(basket_totals_subq.c.basket_total, 0)
                    ),
                    0,
                )
            )
            .select_from(CartItem)
            .outerjoin(
                basket_totals_subq,
                basket_totals_subq.c.basket_id == CartItem.basket_id,
            )
            .where(CartItem.cart_id == cart_id)
        )
        return round(float(result.scalar() or 0), 2)

    async def get_or_create(
        self, user_id: Optional[str] = None, session_id: Optional[str] = None
    ) -> Cart:

        cart = None
        if user_id:
            cart = await self.get_by_user(user_id)
        elif session_id:
            cart = await self.get_by_session(session_id)

        if cart is None:
            cart = Cart(user_id=user_id, session_id=session_id)
            self.db.add(cart)
            await self.db.flush()

            set_committed_value(cart, "items", [])

        return cart

class CartItemRepository(BaseRepository[CartItem]):

    model = CartItem

    def __init__(self, db: AsyncSession):
        super().__init__(db)

    async def clear_cart(self, cart_id: str) -> int:

        result = await self.db.execute(
            delete(CartItem).where(CartItem.cart_id == cart_id)
        )
        await self.db.flush()
        return int(result.rowcount or 0)