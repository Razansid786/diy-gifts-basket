"""
app/repositories/user_repo.py
─────────────────────────────
Data-access layer for the ``users`` table.
"""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for user CRUD and lookup queries."""

    model = User

    def __init__(self, db: AsyncSession):
        super().__init__(db)

    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Look up a user by their email address.

        Used during login to verify credentials (FR2).
        """
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalars().first()
