from app.schemas.base.response_schemas import SuccessfulResponse
from app.schemas.task_schemas import Task


class TaskResponse(SuccessfulResponse):
    data: list[Task]
    