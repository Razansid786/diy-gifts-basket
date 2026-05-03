
from typing import List

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.address import Address
from app.repositories.base import BaseRepository

class AddressRepository(BaseRepository[Address]):

    model = Address

    def __init__(self, db: AsyncSession):
        super().__init__(db)

    async def get_by_user(self, user_id: str) -> List[Address]:

        result = await self.db.execute(
            select(Address)
            .where(Address.user_id == user_id)
            .order_by(Address.created_at.desc())
        )
        return list(result.scalars().all())

    async def clear_default(self, user_id: str) -> None:

        await self.db.execute(
            update(Address)
            .where(Address.user_id == user_id, Address.is_default.is_(True))
            .values(is_default=False)
        )
        await self.db.flush()