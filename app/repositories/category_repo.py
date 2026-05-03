
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.repositories.base import BaseRepository

class CategoryRepository(BaseRepository[Category]):

    model = Category

    def __init__(self, db: AsyncSession):
        super().__init__(db)

    async def get_by_slug(self, slug: str) -> Optional[Category]:

        result = await self.db.execute(
            select(Category).where(Category.slug == slug)
        )
        return result.scalars().first()