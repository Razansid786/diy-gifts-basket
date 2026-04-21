"""
app/repositories/category_repo.py
──────────────────────────────────
Data-access layer for the ``categories`` table (FR7).
"""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.repositories.base import BaseRepository


class CategoryRepository(BaseRepository[Category]):
    """Repository for category CRUD and slug lookup."""

    model = Category

    def __init__(self, db: AsyncSession):
        super().__init__(db)

    async def get_by_slug(self, slug: str) -> Optional[Category]:
        """Look up a category by its URL-friendly slug."""
        result = await self.db.execute(
            select(Category).where(Category.slug == slug)
        )
        return result.scalars().first()
