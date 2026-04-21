"""
app/utils/pagination.py
───────────────────────
Reusable pagination helpers for list endpoints.
"""

from typing import Optional

from fastapi import Query


class PaginationParams:
    """
    FastAPI dependency for standard pagination query parameters.

    Usage::

        @router.get("/items")
        async def list_items(pagination: PaginationParams = Depends()):
            items = await repo.get_all(
                skip=pagination.skip,
                limit=pagination.limit,
            )

    Query params:
        skip  — Number of items to skip (default 0).
        limit — Maximum items to return (default 50, max 100).
    """

    def __init__(
        self,
        skip: int = Query(0, ge=0, description="Number of items to skip."),
        limit: int = Query(50, ge=1, le=100, description="Max items to return."),
    ):
        self.skip = skip
        self.limit = limit
