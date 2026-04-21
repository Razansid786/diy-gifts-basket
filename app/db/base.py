"""
app/db/base.py
──────────────
Single import point for the SQLAlchemy ``DeclarativeBase``.

Every ORM model inherits from ``Base`` defined here.  Keeping it in
its own file prevents circular-import issues when Alembic or other
modules need access to ``Base.metadata``.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    Abstract declarative base for all ORM models.

    SQLAlchemy 2.x style — models use ``Mapped[]`` type annotations
    and ``mapped_column()`` instead of the legacy ``Column()`` API.
    """
    pass
