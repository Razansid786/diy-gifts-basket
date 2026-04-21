"""
app/repositories/cart_repo.py
─────────────────────────────
Data-access layer for the ``carts`` and ``cart_items`` tables (FR22).
"""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.cart import Cart, CartItem
from app.repositories.base import BaseRepository


class CartRepository(BaseRepository[Cart]):
    """Repository for cart operations."""

    model = Cart

    def __init__(self, db: AsyncSession):
        super().__init__(db)

    async def get_by_user(self, user_id: str) -> Optional[Cart]:
        """Get the single cart for a registered user (creates if absent)."""
        result = await self.db.execute(
            select(Cart)
            .options(selectinload(Cart.items))
            .where(Cart.user_id == user_id)
        )
        return result.scalars().first()

    async def get_by_session(self, session_id: str) -> Optional[Cart]:
        """Get the cart for a guest session."""
        result = await self.db.execute(
            select(Cart)
            .options(selectinload(Cart.items))
            .where(Cart.session_id == session_id)
        )
        return result.scalars().first()

    async def get_or_create(
        self, user_id: Optional[str] = None, session_id: Optional[str] = None
    ) -> Cart:
        """
        Return the existing cart or create a new one.

        Ensures every user/session has exactly one cart.
        """
        cart = None
        if user_id:
            cart = await self.get_by_user(user_id)
        elif session_id:
            cart = await self.get_by_session(session_id)

        if cart is None:
            cart = await self.create({
                "user_id": user_id,
                "session_id": session_id,
            })
            # Re-fetch with items loaded
            if user_id:
                cart = await self.get_by_user(user_id)
            else:
                cart = await self.get_by_session(session_id)

        return cart


class CartItemRepository(BaseRepository[CartItem]):
    """Repository for cart line items."""

    model = CartItem

    def __init__(self, db: AsyncSession):
        super().__init__(db)
