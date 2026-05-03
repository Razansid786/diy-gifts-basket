
from typing import Optional

from fastapi import Query

class PaginationParams:

    def __init__(
        self,
        skip: int = Query(0, ge=0, description="Number of items to skip."),
        limit: int = Query(50, ge=1, le=100, description="Max items to return."),
    ):
        self.skip = skip
        self.limit = limit