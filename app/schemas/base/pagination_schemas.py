from typing import Annotated
from fastapi import Query, Depends


class PaginationParams:
    def __init__(
        self,
        page: Annotated[int, Query(ge=1, description="Page number")] = 1,
        per_page: Annotated[int, Query(ge=1, le=50, description="Amount of records on page")] = 20,
    ):
        self.page = page
        self.per_page = per_page
        self.offset = (page - 1) * per_page
        self.limit = per_page