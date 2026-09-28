from uuid import UUID
from typing import Annotated

from fastapi import APIRouter, Request, Header, status, Query

from app.libs.auth import validate_permissions
from app.libs.auth.token import token_info
from app.libs.nestorlog import nlog

from app.exceptions.main_exceptions import NotImplementedException

from app.schemas.base.response_schemas import ResponseDetail, ResponseInfo, SuccessfulResponse
from app.schemas.task_response_schemas import TaskResponse
from app.schemas.task_schemas import AddTaskModel, UpdateTaskModel, UpdateTaskStatus

from app.services.base.utils import HeaderAlias
from app.services.task_service import task_service


router = APIRouter(tags=["Задания"])


@router.get(
        "/account/my/tasks",
        response_model=TaskResponse, 
        response_model_exclude_none=True, 
        summary='Get tasks in my account'
    )
@nlog
@validate_permissions("GET_ACCOUNT_MY_TASKS")
async def get_my_account_tasks(
    request: Request,
    project_id: Annotated[UUID, Header(alias=HeaderAlias.PROJECT_ID)],
    process_id: UUID | None = None
) -> TaskResponse:
    token = token_info(request)
    account_id = token.account_id
    
    tasks = await task_service.get_items(
        request=request, account_id=account_id, project_id=project_id, process_id=process_id
    )

    response = TaskResponse(
        detail=ResponseDetail(
            code='OK',
            message='Tasks received'
        ),
        data=tasks,
        info=ResponseInfo(
            count=len(tasks)
        )
    )
    return response


@router.get(
        "/account/{account_id}/tasks",
        response_model=TaskResponse, 
        response_model_exclude_none=True, 
        summary='Get account tasks'
    )
@nlog
@validate_permissions("GET_ACCOUNT_ACCOUNT_ID_TASKS")
async def get_tasks(
    request: Request,
    account_id: UUID,
    project_id: Annotated[UUID, Header(alias=HeaderAlias.PROJECT_ID)],
    process_id: UUID | None = None,
    user_id: UUID | None = None,
    task_ids: str = Query(
        default=None,
        description="Several comma separated IDs can be specified."
    )
) -> TaskResponse:
    
    tasks = await task_service.get_items(
        request=request, 
        account_id=account_id, 
        project_id=project_id, 
        process_id=process_id, 
        user_id=user_id, 
        task_ids=task_ids
    )

    response = TaskResponse(
        detail=ResponseDetail(
            code='OK',
            message='Tasks received'
        ),
        data=tasks,
        info=ResponseInfo(
            count=len(tasks)
        )
    )
    return response


@router.get(
        "/account/my/task/{task_id}", 
        response_model=TaskResponse, 
        response_model_exclude_none=True, 
        summary='Get task by id in my account'
    )
@nlog
@validate_permissions("GET_ACCOUNT_MY_TASK_TASK_ID")
async def get_my_account_task(
    request: Request,
    task_id: UUID,
    project_id: Annotated[UUID, Header(alias=HeaderAlias.PROJECT_ID)]
) -> TaskResponse:
    token = token_info(request)
    account_id = token.account_id

    task = await task_service.get_item(
        request=request, account_id=account_id, task_id=task_id, project_id=project_id
    )

    response = TaskResponse(
        detail=ResponseDetail(
            code='OK',
            message='Task received'
        ),
        data=[task],
        info=ResponseInfo()
    )
    return response


@router.get(
        "/account/{account_id}/task/{task_id}", 
        response_model=TaskResponse, 
        response_model_exclude_none=True, 
        summary='Get task by id'
    )
@nlog
@validate_permissions("GET_ACCOUNT_ACCOUNT_ID_TASK_TASK_ID")
async def get_task(
    request: Request,
    account_id: UUID,
    task_id: UUID,
    project_id: Annotated[UUID, Header(alias=HeaderAlias.PROJECT_ID)]
) -> TaskResponse:
    task = await task_service.get_item(
        request=request, account_id=account_id, task_id=task_id, project_id=project_id
    )

    response = TaskResponse(
        detail=ResponseDetail(
            code='OK',
            message='Task received'
        ),
        data=[task],
        info=ResponseInfo()
    )
    return response


@router.post(
    '/task', 
    status_code=status.HTTP_201_CREATED, 
    response_model=TaskResponse, 
    response_model_exclude_none=True, 
    summary='Create task'
)
@nlog
@validate_permissions("POST_TASK")
async def create_task(
    request: Request,
    data: AddTaskModel,
    project_id: Annotated[UUID, Header(alias=HeaderAlias.PROJECT_ID)]
) -> TaskResponse:
    token = token_info(request)
    account_id = token.account_id

    task = await task_service.create_item(
        request=request, item_data=data, project_id=project_id, account_id=account_id, user_id=token.user_id
    )

    return TaskResponse(
        detail=ResponseDetail(
            code='OK',
            message='Task created'
        ),
        data=[task],
        info=ResponseInfo()
    )


@router.patch('/account/my/task/{task_id}', 
    response_model=TaskResponse, 
    response_model_exclude_none=True, 
    summary='Update task in my account'
)
@nlog
@validate_permissions("PATCH_ACCOUNT_MY_TASK_TASK_ID")
async def update_my_account_task(
    request: Request,
    task_id: UUID,
    data: UpdateTaskModel,
    project_id: Annotated[UUID, Header(alias=HeaderAlias.PROJECT_ID)]
) -> TaskResponse:
    token = token_info(request)
    account_id = token.account_id

    task = await task_service.update_item(
        request=request, task_id=task_id, data=data, project_id=project_id, account_id=account_id
    )

    return TaskResponse(
        detail=ResponseDetail(
            code='OK',
            message='Task updated'
        ),
        data=[task],
        info=ResponseInfo()
    )


@router.patch('/account/{account_id}/task/{task_id}', 
    response_model=TaskResponse, 
    response_model_exclude_none=True, 
    summary='Update task'
)
@nlog
@validate_permissions("PATCH_ACCOUNT_ACCOUNT_ID_TASK_TASK_ID")
async def update_task(
    request: Request,
    account_id: UUID,
    task_id: UUID,
    data: UpdateTaskModel,
    project_id: Annotated[UUID, Header(alias=HeaderAlias.PROJECT_ID)]
) -> TaskResponse:
    
    task = await task_service.update_item(
        request=request, task_id=task_id, data=data, project_id=project_id, account_id=account_id
    )

    return TaskResponse(
        detail=ResponseDetail(
            code='OK',
            message='Task updated'
        ),
        data=[task],
        info=ResponseInfo()
    )


@router.patch('/account/my/task/{task_id}/status', 
    response_model=SuccessfulResponse, 
    response_model_exclude_none=True, 
    summary='Change task status in my account'
)
@nlog
@validate_permissions("PATCH_ACCOUNT_MY_TASK_TASK_ID_STATUS")
async def update_my_account_task_status(
    request: Request,
    task_id: UUID,
    data: UpdateTaskStatus,
    project_id: Annotated[UUID, Header(alias=HeaderAlias.PROJECT_ID)]
) -> SuccessfulResponse:
    token = token_info(request)
    account_id = token.account_id

    await task_service.update_task_status(
        request=request, task_id=task_id, data=data, project_id=project_id, account_id=account_id
    )

    return SuccessfulResponse(
        detail=ResponseDetail(
            code='OK',
            message='Task status changed'
        ),
        info=ResponseInfo()
    )


@router.patch('/account/{account_id}/task/{task_id}/status', 
    response_model=SuccessfulResponse, 
    response_model_exclude_none=True, 
    summary='Change task status'
)
@nlog
@validate_permissions("PATCH_ACCOUNT_ACCOUNT_ID_TASK_TASK_ID_STATUS")
async def update_task_status(
    request: Request,
    account_id: UUID,
    task_id: UUID,
    data: UpdateTaskStatus,
    project_id: Annotated[UUID, Header(alias=HeaderAlias.PROJECT_ID)]
) -> SuccessfulResponse:
    
    await task_service.update_task_status(
        request=request, task_id=task_id, data=data, project_id=project_id, account_id=account_id
    )

    return SuccessfulResponse(
        detail=ResponseDetail(
            code='OK',
            message='Task status changed'
        ),
        info=ResponseInfo()
    )
