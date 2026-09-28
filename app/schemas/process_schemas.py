from uuid import UUID
from enum import StrEnum

from pydantic import BaseModel


class ProcessRegistry(StrEnum):
    PROCESS = "process"
    PROCESSES = "processes"


class Process(BaseModel):
    process_id: UUID
    process_key: str
    title: str
    description: str
    