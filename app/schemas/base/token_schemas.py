from enum import StrEnum, IntEnum
from uuid import UUID

from pydantic import BaseModel

class TokenInfo(BaseModel):
    project_id: UUID
    account_id: UUID | None = None
    user_id: UUID | None = None
    profile_id: UUID | None = None
    device_id: UUID | str | None = None
    organizations: list | None = None
    permissions: dict | set | None = None
    groups: list | set | None = None