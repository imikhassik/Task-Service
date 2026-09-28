from uuid import UUID
from enum import StrEnum
from datetime import datetime

from pydantic import BaseModel

from app.schemas.profile_schemas import Profile
from app.schemas.process_schemas import Process
from app.schemas.attachment_schemas import Attachment


class TaskType(StrEnum):
    TASK = "task"


class TaskRegistry(StrEnum):
    TASK = "task"
    TASKS = "tasks"


class TaskStatus(StrEnum):
    DRAFT = "draft"
    IN_PROGRESS = "in progress"
    APPROVED = "approved"
    REJECTED = "rejected"


class AssigneeType(StrEnum):
    PROFILE = "profile"
    TEAM = "team"


class TaskLink(StrEnum):
    TASK_ASSIGNEE = "task_{assignee}"

    def resolve(self, **kwargs):
        return self.value.format(**kwargs)


class Assignee(BaseModel):
    assignee_id: UUID
    assignee_type: AssigneeType


class UpdateTaskStatus(BaseModel):
    status: TaskStatus


class AddTaskModel(BaseModel):
    process_id: UUID
    title: str
    description: str | None = None
    fields: dict
    assignee: list[Assignee] | None = None


class UpdateTaskModel(BaseModel):
    title: str | None = None
    description: str | None = None
    fields: dict | None = None


class Task(BaseModel):
    task_id: UUID
    status: TaskStatus
    task_key: str
    title: str
    description: str | None = None
    author: Profile
    # Return id and type if can't find real assignee object
    assignee: list[dict | Assignee | Profile] | None = None
    process: Process
    fields: dict
    attachments: list[Attachment] | None = None
    created_date: datetime
    modified_date: datetime
