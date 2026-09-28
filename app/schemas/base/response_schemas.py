from pydantic import BaseModel, Field

from app.config import settings


class ResponseDetail(BaseModel):
    code: str | None = None
    message: str | None = None


class ExceptionDetail(BaseModel):
    detail: ResponseDetail


class ResponseInfo(BaseModel):
    api_version: str = settings.VERSION
    count: int = None
    total: int = None
    page: int = None
    page_size: int = None

    class Config:
        extra = "allow"


class SuccessfulResponse(BaseModel):
    detail: ResponseDetail
    data: list | None = Field(default=None, examples=[[{}]])
    info: ResponseInfo
