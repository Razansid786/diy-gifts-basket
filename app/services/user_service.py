"""
app/services/user_service.py
────────────────────────────
Business logic for user profile management.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.schemas.user import UserUpdate, UserResponse


class UserService:
    """Handles user profile reads and updates."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)

    async def get_profile(self, user_id: str) -> User:
        """
        Return the full user profile.

        Raises ``NotFoundError`` if the user does not exist.
        """
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("User", user_id)
        return user

    async def update_profile(self, user_id: str, data: UserUpdate) -> User:
        """
        Update editable fields on the user's profile.

        Only non-None fields in ``data`` are applied (partial update).
        """
        update_data = data.model_dump(exclude_unset=True)
        user = await self.user_repo.update(user_id, update_data)
        if not user:
            raise NotFoundError("User", user_id)
        return user
