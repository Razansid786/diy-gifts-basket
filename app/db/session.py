"""
app/db/session.py
─────────────────
Async database engine and session factory for Supabase PostgreSQL.

Key design decisions
~~~~~~~~~~~~~~~~~~~~
* ``prepared_statement_cache_size=0`` — required when connecting via
  Supabase's transaction-mode pooler (port 6543).
* ``expire_on_commit=False`` — prevents lazy-load errors after commit
  in async code.
* ``get_db()`` is the FastAPI dependency that yields a session per request.
"""

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings

settings = get_settings()

# ── Async engine ─────────────────────────────────────────────────────
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,          # log SQL in debug mode
    pool_size=20,
    max_overflow=0,
    connect_args={
        # Required for Supabase transaction-mode pooler (port 6543)
        "server_settings": {"jit": "off"},
        "prepared_statement_cache_size": 0,
    },
)

# ── Session factory ──────────────────────────────────────────────────
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db():
    """
    FastAPI dependency that provides a scoped async database session.

    The session is automatically closed when the request finishes,
    regardless of whether an exception occurred.

    Usage::

        @router.get("/items")
        async def list_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
