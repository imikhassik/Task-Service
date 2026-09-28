from uuid import UUID
from datetime import date

from pydantic import BaseModel

from app.schemas.base.base_schemas import RegistryDataTitleValue


class Competition(BaseModel):
    quest_id: UUID
    category: str | None = None
    materials: list[RegistryDataTitleValue] | None = None
    urls: list[RegistryDataTitleValue] | None = None
    media: list[RegistryDataTitleValue] | None = None


class Participant(BaseModel):
    first_name: str
    last_name: str
    middle_name: str | None = None
    birth_date: date | None = None
    contact_phone: str | None = None
    contact_email: str | None = None
    registration_address: str | None = None
    education: str | None = None
    specialty: str | None = None
    personal_data_consent: bool = False
    photo_main: str | None = None


class Organization(BaseModel):
    organization_id: UUID
    specialty_title: str
    start_work_date: date


class Application(BaseModel):
    competition: Competition
    participant: Participant
    organization: Organization
    