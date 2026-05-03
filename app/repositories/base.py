
from typing import Generic, List, Optional, Type, TypeVar

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base

ModelType = TypeVar("ModelType", bound=Base)

class BaseRepository(Generic[ModelType]):

    def __init__(self, db: AsyncSession, model: Optional[Type[ModelType]] = None):
        self.db = db

        if model is not None:
            self.model = model

    async def create(self, obj_data: dict) -> ModelType:

        instance = self.model(**obj_data)
        self.db.add(instance)
        await self.db.flush()
        return instance

    async def get_by_id(self, obj_id: str) -> Optional[ModelType]:

        result = await self.db.execute(
            select(self.model).where(self.model.id == obj_id)
        )
        return result.scalars().first()

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> List[ModelType]:

        result = await self.db.execute(
            select(self.model).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def count(self) -> int:

        result = await self.db.execute(
            select(func.count()).select_from(self.model)
        )
        return result.scalar() or 0

    async def update(self, obj_id: str, update_data: dict) -> Optional[ModelType]:

        instance = await self.get_by_id(obj_id)
        if instance is None:
            return None

        for key, value in update_data.items():
            if value is not None:
                setattr(instance, key, value)

        await self.db.flush()
        return instance

    async def delete(self, obj_id: str) -> bool:

        instance = await self.get_by_id(obj_id)
        if instance is None:
            return False

        await self.db.delete(instance)
        await self.db.flush()
        return True