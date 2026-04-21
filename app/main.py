"""
app/main.py
───────────
FastAPI application entry point.

Responsibilities:
* Create and configure the FastAPI app instance.
* Register CORS middleware for frontend communication.
* Include the versioned API router.
* Register global exception handlers.
* Provide a health-check endpoint.

Run with::

    uvicorn app.main:app --reload
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import v1_router
from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers

# ── Logging setup ────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


# ── Lifespan handler ─────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Runs on startup and shutdown.

    Startup:  Log configuration and verify DB engine.
    Shutdown: Dispose of the engine connection pool.
    """
    settings = get_settings()
    logger.info(f"Starting {settings.APP_NAME} (debug={settings.DEBUG})")
    yield
    # Shutdown — dispose the database engine
    from app.db.session import engine
    await engine.dispose()
    logger.info("Database engine disposed. Goodbye!")


# ── App factory ──────────────────────────────────────────────────────
def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns
    -------
    FastAPI
        The configured application instance.
    """
    settings = get_settings()

    app = FastAPI(
        title=settings.APP_NAME,
        description=(
            "API for the DIY Gift Basket Website — "
            "browse, build, personalize, and order custom gift baskets."
        ),
        version="1.0.0",
        lifespan=lifespan,
    )

    # ── CORS Middleware ──────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],           # Restrict in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Exception handlers ───────────────────────────────────────────
    register_exception_handlers(app)

    # ── Routers ──────────────────────────────────────────────────────
    app.include_router(v1_router)

    # ── Health check ─────────────────────────────────────────────────
    @app.get("/health", tags=["Health"])
    async def health_check():
        """Simple health check endpoint."""
        return {"status": "healthy", "app": settings.APP_NAME}

    return app


# Create the app instance (used by uvicorn)
app = create_app()
