from enum import StrEnum, IntEnum
from uuid import UUID

from pydantic import BaseModel


class RegistryDataTitleValue(BaseModel):
    title: str
    value: str


class RegistryObjectStatus(StrEnum):
    ACTIVE = "active"
    HIDDEN = "inactive"


class Meta(BaseModel):
    status: str = RegistryObjectStatus.ACTIVE
    flags: int = 0
    internal_id: int | None = None
    key_version: int | str | None = None

    class Config:
        extra = "allow"


class RegistryObject(BaseModel):
    id: UUID | None = None
    object_code: str | None = None
    object_type: str | None = None
    object_item: UUID | None = None
    data: dict | None = None
    meta: Meta | None = None
    project_id: UUID | None = None
    account_id: UUID | None = None
    user_id: UUID | None = None


class LinkObject(BaseModel):
    id: UUID | None = None
    link_code: str | None = None
    link_type: str | None = None
    object1: UUID | None = None
    object2: UUID | None = None
    weight: float | None = None
    direction: int | None = None
    meta: Meta | None = None
    data: dict | None = None
    project_id: UUID | None = None
    account_id: UUID | None = None
    user_id: UUID | None = None


class ItemStatus(StrEnum):
    ACTIVE = RegistryObjectStatus.ACTIVE
    HIDDEN = RegistryObjectStatus.HIDDEN


class LinkStatus(StrEnum):
    ACTIVE = RegistryObjectStatus.ACTIVE
    HIDDEN = RegistryObjectStatus.HIDDEN


class LinkHandle(StrEnum):
    LINK = "link"
    LINKS = "links"


class LinkFields(IntEnum):
    #  Default link weight (0 to 1)
    WEIGHT = 0
    #   Default link direction:
    #       00: no link, 01: object1 -> object2, 10: object1 <- object1, 11 object1 <-> object2
    DIRECTION = 3