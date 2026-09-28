from uuid import UUID
from enum import StrEnum
from datetime import datetime

from pydantic import BaseModel, AnyUrl


class AttachmentType(StrEnum):
    IMAGE = "image"


class ContentType(StrEnum):
    IMAGE_PNG = "image/png"


class Attachment(BaseModel):
    attachment_id: UUID
    title: str
    url: AnyUrl
    attachment_type: AttachmentType
    content_type: ContentType
    created_date: datetime
    modified_date: datetime
    