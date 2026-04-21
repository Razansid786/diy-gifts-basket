"""
app/repositories/base.py
────────────────────────
Generic CRUD repository base class.

Follows the **Repository Pattern** (part of the Single Responsibility
Principle) — all raw database interactions live here, keeping service
and API layers clean.

Every domain-specific repository (e.g. ``UserRepository``) extends
this class and inherits basic CRUD operations.  Custom queries are
added as additional methods in the child class.
"""

from typing import Generic, List, Optional, Type, TypeVar

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base

# Type variable bound to SQLAlchemy models
ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """
    Generic async CRUD repository.

    Parameters
    ----------
    model : Type[ModelType]
        The SQLAlchemy ORM model class this repository manages.
    db : AsyncSession
        The database session for the current request.
    """

    def __init__(self, db: AsyncSession, model: Optional[Type[ModelType]] = None):
        self.db = db
        # Allow subclasses to set ``model`` as a class attribute
        if model is not None:
            self.model = model

    # ── CREATE ───────────────────────────────────────────────────────

    async def create(self, obj_data: dict) -> ModelType:
        """
        Insert a new row and return the ORM instance.

        Parameters
        ----------
        obj_data : dict
            Column values for the new row (e.g. from ``schema.model_dump()``).
        """
        instance = self.model(**obj_data)
        self.db.add(instance)
        await self.db.commit()
        await self.db.refresh(instance)
        return instance

    # ── READ ─────────────────────────────────────────────────────────

    async def get_by_id(self, obj_id: str) -> Optional[ModelType]:
        """Fetch a single row by its primary key, or ``None``."""
        result = await self.db.execute(
            select(self.model).where(self.model.id == obj_id)
        )
        return result.scalars().first()

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> List[ModelType]:
        """Return a paginated list of rows."""
        result = await self.db.execute(
            select(self.model).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def count(self) -> int:
        """Return the total number of rows in the table."""
        result = await self.db.execute(
            select(func.count()).select_from(self.model)
        )
        return result.scalar() or 0

    # ── UPDATE ───────────────────────────────────────────────────────

    async def update(self, obj_id: str, update_data: dict) -> Optional[ModelType]:
        """
        Update specific columns on an existing row.

        Parameters
        ----------
        obj_id : str
            Primary key of the row to update.
        update_data : dict
            Key-value pairs of columns to change.
            Keys with ``None`` values are skipped (partial update).

        Returns
        -------
        Optional[ModelType]
            The refreshed ORM instance, or ``None`` if not found.
        """
        instance = await self.get_by_id(obj_id)
        if instance is None:
            return None

        for key, value in update_data.items():
            if value is not None:
                setattr(instance, key, value)

        await self.db.commit()
        await self.db.refresh(instance)
        return instance

    # ── DELETE ────────────────────────────────────────────────────────

    async def delete(self, obj_id: str) -> bool:
        """
        Delete a row by primary key.

        Returns ``True`` if the row existed and was deleted.
        """
        instance = await self.get_by_id(obj_id)
        if instance is None:
            return False

        await self.db.delete(instance)
        await self.db.commit()
        return True
