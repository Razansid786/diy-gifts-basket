from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from app.core.config import get_settings

settings = get_settings()
database_url = settings.DATABASE_URL
if "prepared_statement_cache_size" not in database_url:
    separator = "&" if "?" in database_url else "?"
    database_url += f"{separator}prepared_statement_cache_size=0"

engine = create_async_engine(
    database_url,
    echo=False,
    pool_size=10,
    max_overflow=5,
    pool_recycle=300,
    connect_args={
        "server_settings": {"jit": "off"},
        "statement_cache_size": 0,
    },
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()