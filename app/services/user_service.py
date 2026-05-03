
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.schemas.user import UserUpdate, UserResponse

class UserService:

    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)

    async def get_profile(self, user_id: str) -> User:

        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("User", user_id)
        return user

    async def update_profile(self, user_id: str, data: UserUpdate) -> User:

        update_data = data.model_dump(exclude_unset=True)
        user = await self.user_repo.update(user_id, update_data)
        if not user:
            raise NotFoundError("User", user_id)
        return user