from uuid import UUID

from pydantic import BaseModel

from app.config import settings


class Info(BaseModel):
    version: str = settings.VERSION
