from uuid import UUID

from pydantic import BaseModel

from app.schemas.base.base_schemas import RegistryDataTitleValue


class Profile(BaseModel):
    profile_id: UUID
    first_name: str | None = None
    last_name: str | None = None
    middle_name: str | None = None
    contact_phone: list[RegistryDataTitleValue] | None = None
    contact_email: list[RegistryDataTitleValue] | None = None
