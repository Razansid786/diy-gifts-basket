"""
app/repositories/address_repo.py
────────────────────────────────
Data-access layer for the ``addresses`` table (FR4).
"""

from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.address import Address
from app.repositories.base import BaseRepository


class AddressRepository(BaseRepository[Address]):
    """Repository for shipping address CRUD."""

    model = Address

    def __init__(self, db: AsyncSession):
        super().__init__(db)

    async def get_by_user(self, user_id: str) -> List[Address]:
        """Return all addresses belonging to a user, ordered by creation date."""
        result = await self.db.execute(
            select(Address)
            .where(Address.user_id == user_id)
            .order_by(Address.created_at.desc())
        )
        return list(result.scalars().all())

    async def clear_default(self, user_id: str) -> None:
        """
        Set ``is_default = False`` on all addresses for a user.

        Called before marking a new address as default to ensure
        only one address is default at a time.
        """
        addresses = await self.get_by_user(user_id)
        for addr in addresses:
            if addr.is_default:
                addr.is_default = False
        await self.db.commit()
