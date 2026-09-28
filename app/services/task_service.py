import asyncio
import logging


from typing import Any
from uuid import UUID
from collections import defaultdict


from fastapi import Request


from app.exceptions.main_exceptions import NotFoundException
from app.exceptions.sub_exceptions.failed_dependency_exceptions import (
    FailedLinkingException,
    RegistryInteractionException,
)
from app.exceptions.sub_exceptions.not_found_exceptions import ProcessNotFoundException, TaskNotFoundException, \
TasksNotFoundException
from app.exceptions.sub_exceptions.bad_logic_exceptions import InvalidStatusUpdateException


from app.services.base.registry.items import ItemsService
from app.services.base.registry.links import LinksService
from app.services.base.utils import Method, Handle, generate_object_code
from app.services.base.service.api_interaction import interact_with_api


from app.schemas.task_schemas import TaskRegistry, Task, TaskStatus, AddTaskModel, TaskType, Assignee, TaskLink, \
    AssigneeType, UpdateTaskModel, UpdateTaskStatus
from app.schemas.profile_schemas import Profile
from app.schemas.process_schemas import Process, ProcessRegistry
from app.schemas.attachment_schemas import Attachment
from app.schemas.base.base_schemas import RegistryObjectStatus, ItemStatus


from app.config import settings


logger = logging.getLogger(__name__)



class TaskService:
    # Service for working with processes and tasks.


    def __init__(self, base_registry_url: str | None = None):
        # Task service initialization.
        # Input parameters:
        #   base_registry_url: str | None - registry URL (optional)
        self.tasks_service = ItemsService(
            single_name=TaskRegistry.TASK,
            plural_name=TaskRegistry.TASKS,
            base_registry_url=base_registry_url,
        )
        self.processes_service = ItemsService(
            single_name=ProcessRegistry.PROCESS,
            plural_name=ProcessRegistry.PROCESSES,
            base_registry_url=base_registry_url,
        )


        self.links_service = LinksService(base_registry_url=base_registry_url)


    # Converts a dictionary from the registry into a TaskModel object.
    # Input parameters:
    #   data: dict - dictionary with template data from the registry
    #   extra: dict | None - additional data (for example, link data)
    # Output parameters:
    #  TaskModel - serialized task object
    def _serialize_task(self, data: dict, extra: dict | None = None) -> Task:
        task_data = data.get("data", {})
        meta_data = data.get("meta", {})
        status = TaskStatus.DRAFT if meta_data.get("status") == RegistryObjectStatus.ACTIVE else meta_data.get("status")
        task_key = extra.get("process").process_key + "-" + str(meta_data.get("internal_id"))
        return Task(
            task_id=data.get('id'),
            status=status,
            task_key=task_key,
            title=task_data.get("title"),
            description=task_data.get("description"),
            author=extra.get("author"),
            assignee=extra.get("assignee"),
            process=extra.get("process"),
            fields=task_data.get("fields"),
            attachments=extra.get("attachments"),
            created_date=data.get("created_date"),
            modified_date=data.get("modified_date")
        )
    
    def _serialize_process(self, data: dict) -> Process:
        process_data = data.get("data", {})
        return Process(
            process_id=data.get("id"),
            process_key=process_data.get("process_key"),
            title=process_data.get("title"),
            description=process_data.get("description")
        )
    
    def _serialize_profile(self, data: dict) -> Profile:
        return Profile(
            profile_id=data.get("profile_id"),
            first_name=data.get("first_name"),
            last_name=data.get("last_name"),
            middle_name=data.get("middle_name"),
            contact_phone=data.get("contact_phone"),
            contact_email=data.get("contact_email")
        )
    
    # Retrieves a list of tasks in an account. Attachments are not displayed in list tasks
    async def get_items(
            self, request: Request, 
            account_id: UUID, 
            project_id: UUID, 
            process_id: UUID | None = None,
            user_id: UUID | None = None, 
            task_ids: str | None = None
        ) -> list[Task]:
        check_user = False
        if user_id:
            check_user = True
        if task_ids:
            task_ids = task_ids.split(",")
        
        try:
            response = await self.tasks_service.items(
                request=request, 
                project_id=project_id,
                account_id=account_id, 
                user_id=user_id, 
                check_user=check_user,
                ids=task_ids,
                object_item=process_id
            )
            all_tasks = response.get("results")


            #  Filter out deleted tasks
            tasks = [task for task in all_tasks if task.get("meta").get("status") != ItemStatus.HIDDEN]
            if not tasks:
                raise NotFoundException
        except NotFoundException:
            raise TasksNotFoundException


        return await self._enrich_entries(request=request, tasks=tasks, project_id=project_id, account_id=account_id)


    async def get_item(
            self, request: Request, account_id: UUID, project_id: UUID, task_id: UUID
    ) -> Task:
        task = await self._get_task_object(
            request=request, account_id=account_id, task_id=task_id, project_id=project_id
        )
        process = await self._get_process(
            request=request, process_id=task.get("object_item"), project_id=project_id, account_id=account_id
        )
        author = await self._get_profile(request=request, profile_id=task.get("user_id"))
        assignee = await self._get_assignee(
            request=request, task_id=task_id, account_id=account_id, project_id=project_id
        )
        extra = {
            "process": process,
            "author": author,
            "assignee": assignee
        }
        return self._serialize_task(data=task, extra=extra)


    async def create_item(
            self, request: Request, item_data: AddTaskModel, project_id: UUID, account_id: UUID, user_id: UUID
        ) -> Task:
        process = await self._get_process(
            request=request, process_id=item_data.process_id, project_id=project_id, account_id=account_id
        )


        data: dict[str, Any] = {
            "title": item_data.title,
            "fields": item_data.fields
        }
        if item_data.description is not None:
            data["description"] = item_data.description


        task_entry = await self.tasks_service.create(
            request=request,
            object_type=TaskType.TASK,
            object_item=item_data.process_id,
            data=data,
            project_id=project_id,
            account_id=account_id,
            user_id=user_id
        )


        assignee = None
        # If an assignee list is provided, create links
        if item_data.assignee is not None:
            task_id = task_entry.get("id")
            if task_id:
                await self._link_to_assignee(
                    request=request,
                    task_id=UUID(task_id),
                    assignee=item_data.assignee,
                    project_id=project_id,
                    account_id=account_id,
                    user_id=user_id
                )
            
            assignee = await self._get_assignee_by_type(request=request, assignee=item_data.assignee)


        # WORKAROUND: If fields contain competition and organization, create links to optimize search from the quests service
        quest_api_links_service = LinksService(base_registry_url=settings.QUEST_API_REGISTRY_URL)
        if item_data.fields.get("competition"):
            competition_id = item_data.fields.get("competition").get("quest_id")
            await quest_api_links_service.create(
                request=request,
                link_type="task_competition",
                object1=task_entry.get("id"),
                object2=competition_id,
                project_id=project_id,
                account_id=account_id,
                user_id=user_id
            )


        if item_data.fields.get("organization"):
            organization_id = item_data.fields.get("organization").get("organization_id")
            await quest_api_links_service.create(
                request=request,
                link_type="task_organization",
                object1=task_entry.get("id"),
                object2=organization_id,
                project_id=project_id,
                account_id=account_id,
                user_id=user_id
            )


        try:
            author = await self._get_profile(request=request, profile_id=user_id)
        except Exception:
            author = Profile(profile_id=user_id)


        extra = {
            "process": process,
            "author": author
        }


        if assignee:
            extra["assignee"] = assignee


        return self._serialize_task(data=task_entry, extra=extra)


    async def update_item(
            self, request: Request, task_id: UUID, data: UpdateTaskModel, project_id: UUID, account_id: UUID
        ) -> Task:
        task = await self._get_task_object(request=request, account_id=account_id, project_id=project_id, task_id=task_id)
        process = await self._get_process(
            request=request, process_id=task.get("object_item"), project_id=project_id, account_id=account_id
        )
        author = await self._get_profile(request=request, profile_id=task.get("user_id"))
        assignee = await self._get_assignee(
            request=request, task_id=task_id, account_id=account_id, project_id=project_id
        )
        extra = {
            "process": process,
            "author": author,
            "assignee": assignee
        }


        if data.title:
            task["data"]["title"] = data.title
        if data.description is not None:
            task["data"]["description"] = data.description
        if data.fields:
            self._deep_patch(task["data"]["fields"], data.fields)


        task = await self.tasks_service.update(
            request=request, object_id=task_id, data=task,project_id=project_id, account_id=account_id, check_user=False
        )
        
        return self._serialize_task(data=task, extra=extra)
    
    async def update_task_status(
            self, request: Request, task_id: UUID, data: UpdateTaskStatus, project_id: UUID, account_id: UUID
        ) -> Task:
        processing_required = await self._validate_status_change(
            request=request, task_id=task_id, new_status=data.status, project_id=project_id, account_id=account_id
        )
        await self.tasks_service.set_status(
            request=request, 
            object_id=task_id,
            status=data.status if data.status != TaskStatus.DRAFT else ItemStatus.ACTIVE,
            project_id=project_id,
            account_id=account_id,
            check_user=False
        )


        if processing_required:
            asyncio.create_task(self._process_task(request=request, task_id=task_id, status=data.status))
    
    async def _enrich_entries(
            self, request: Request, tasks: list[dict], project_id: UUID, account_id: UUID
        ) -> list[Task]:
        task_ids = [task.get("id") for task in tasks]


        task_process_map = dict()
        task_author_map = dict()
        for task in tasks:
            task_process_map[task.get("id")] = task.get("object_item")
            task_author_map[task.get("id")] = task.get("user_id")


        # Retrieve all processes whose IDs appear in the task records
        processes = await self._get_processes(
            request=request, 
            process_ids=list(set(task_process_map.values())), 
            project_id=project_id, 
            account_id=account_id
        )


        # Collect IDs of task author profiles
        profile_ids = set(task_author_map.values())
        team_ids = set()


        task_assignees = defaultdict(list)
        try:
            # Retrieve links for all found tasks
            response = await self.links_service.links(
                request=request, project_id=project_id, account_id=account_id, check_user=False, object1=",".join(task_ids)
            )
            links = response.get("results")


            for link in links:
                if link.get("link_type") == TaskLink.TASK_ASSIGNEE.resolve(assignee=AssigneeType.PROFILE) or \
                link.get("link_type") == TaskLink.TASK_ASSIGNEE.resolve(assignee=AssigneeType.TEAM):
                    assignee = Assignee(
                            assignee_id=link.get("object2"),
                            assignee_type=link.get("link_type").removeprefix("task_")
                        )
                    # Create a list of assignees for each task
                    task_assignees[link.get("object1")].append(assignee)


                    # If the assignee type is profile, add it to the list of profile IDs to fetch them all at once
                    if assignee.assignee_type == AssigneeType.PROFILE:
                        profile_ids.add(str(assignee.assignee_id))
                    # If the assignee type is team, leave the record as-is for now
                    elif assignee.assignee_type == AssigneeType.TEAM:
                        team_ids.add(str(assignee.assignee_id))


        except NotFoundException:
            pass
        
        # Retrieve all profiles that appear in the tasks
        profiles = await self._get_profiles(request=request, profile_ids=profile_ids)


        # Iterate through the task list and build task models, adding process, author, and assignee models (if they are profiles)
        result = []
        for task in tasks:
            task_id = task.get("id")
            process_id = task_process_map.get(task_id)
            process = processes.get(process_id)


            author_id = task.get("user_id")
            author_profile = profiles.get(author_id)


            assignees = task_assignees.get(task_id)
            
            if assignees:
                for i in range(len(assignees)):
                    assignee = assignees[i]
                    if assignee.assignee_type == AssigneeType.PROFILE:
                        assignees[i] = profiles[str(assignee.assignee_id)]


            extra = {
                "process": process,
                "author": author_profile,
                "assignee": assignees
            }
            result.append(self._serialize_task(data=task, extra=extra))


        return result


    
    def _deep_patch(self, target: dict, patch: dict) -> dict:
        from copy import deepcopy


        for key, value in patch.items():
            if (
                key in target
                and isinstance(target[key], dict)
                and isinstance(value, dict)
            ):
                self._deep_patch(target[key], value)
            else:
                target[key] = deepcopy(value)
        return target


    # Creates a link between a task and an assignee (TASK_{ASSIGNEE}).
    async def _link_to_assignee(
        self,
        request: Request,
        task_id: UUID,
        assignee: list[Assignee],
        project_id: UUID,
        account_id: UUID | None = None,
        user_id: UUID | None = None
    ) -> dict:
        try:
            links = []
            for item in assignee:
                link_code = generate_object_code(project_id, account_id, task_id,item.assignee_id)
                links.append(
                    {
                        "link_type": TaskLink.TASK_ASSIGNEE.resolve(assignee=item.assignee_type),
                        "object1": task_id,
                        "object2": item.assignee_id,
                        "link_code": link_code
                    }
                )


            return await self.links_service.bulk_create(
                request=request,
                links=links,
                project_id=project_id,
                account_id=account_id,
                user_id=user_id
            )
        except RegistryInteractionException as e:
            raise FailedLinkingException(link_type=TaskLink.TASK_ASSIGNEE.resolve(assignee="assignee")) from e


    # Retrieves a process from the registry
    async def _get_process(self, request: Request, process_id: UUID, project_id: UUID, account_id: UUID) -> Process:
        try:
            record = await self.processes_service.get(
                request=request, object_id=process_id, project_id=project_id, account_id=account_id, check_user=False
            )
            return self._serialize_process(data=record)
        except NotFoundException:
            raise ProcessNotFoundException
        
    async def _get_processes(
            self, request: Request, process_ids: list[UUID], project_id: UUID, account_id: UUID
        ) -> dict[UUID, Process]:
        response = await self.processes_service.items(
            request=request, project_id=project_id, account_id=account_id, ids=process_ids, check_user=False
        )
        processes = response.get("results")
        return {process.get("id"): self._serialize_process(process) for process in processes}
        
    # Retrieves a profile from the CP
    async def _get_profile(self, request: Request, profile_id: UUID) -> Profile:
        response, _ = await interact_with_api(
            request=request, 
            method=Method.GET, 
            api_url=settings.USER_PROFILES_API, 
            handle=Handle.PROFILE.resolve(profile_id=profile_id)
        )
        return self._serialize_profile(data=response.get("data")[0])
    
    async def _get_profiles(self, request: Request, profile_ids: set[UUID]) -> dict[UUID, Profile]:
        params = {
            "profile_id": ",".join(profile_ids)
        }
        response, _ = await interact_with_api(
            request=request,
            method=Method.GET,
            api_url=settings.USER_PROFILES_API,
            handle=Handle.PROFILES,
            params=params
        )
        profiles = response.get("data")
        return {profile.get("profile_id"): self._serialize_profile(profile) for profile in profiles}
    
    # Retrieves task_{assignee} links and returns objects or Assignee models if objects are not found
    async def _get_assignee(self, request: Request, task_id: UUID, account_id: UUID, project_id: UUID):
        try:
            response = await self.links_service.links(
                request=request, project_id=project_id, account_id=account_id, check_user=False, object1=task_id
            )
        except NotFoundException:
            return None
        
        links = response.get("results")
        assignee = []
        for link in links:
            assignee.append(
                Assignee(
                    assignee_id=link.get("object2"),
                    assignee_type=link.get("link_type").removeprefix("task_")
                )
            )
        assignee_list = await self._get_assignee_by_type(request=request, assignee=assignee)
        return assignee_list


    
    # Retrieves an object depending on assignee_type. Implemented only for profiles
    async def _get_assignee_by_type(self, request: Request, assignee: list[Assignee]) -> list[dict]:
        result: list[dict] = []


        for item in assignee:
            match item.assignee_type:
                case AssigneeType.PROFILE:
                    try:
                        result.append(await self._get_profile(request=request, profile_id=item.assignee_id))
                    except Exception:
                        result.append(item)
                case _:
                    result.append(item)


        return result
    
    async def _get_task_object(self, request: Request, account_id: UUID, project_id: UUID, task_id: UUID) -> dict:
        try:
            record = await self.tasks_service.get(
                request=request, object_id=task_id, project_id=project_id, account_id=account_id, check_user=False
            )
            return record
        except NotFoundException:
            raise TaskNotFoundException


    async def _validate_status_change(
            self, request: Request, task_id: UUID, new_status: TaskStatus, account_id: UUID, project_id: UUID
        ) -> bool:
        task = await self._get_task_object(
                request=request, account_id=account_id, task_id=task_id, project_id=project_id
            )
        task_status = task.get("meta").get("status")
        processing_required = False


        if task_status == ItemStatus.ACTIVE and new_status == TaskStatus.IN_PROGRESS:
            processing_required = True
        elif task_status == TaskStatus.IN_PROGRESS and new_status != TaskStatus.IN_PROGRESS:
            if new_status == TaskStatus.APPROVED:
                processing_required = True
        elif task_status == TaskStatus.REJECTED and new_status == TaskStatus.DRAFT:
            processing_required = False
        else:
            raise InvalidStatusUpdateException


        return processing_required


    async def _process_task(self, request: Request, task_id: UUID, status: TaskStatus) -> None:
        payload = {
            "task_id": task_id,
            "task_status": status
        }
        try:
            await interact_with_api(
                request=request,
                method=Method.POST,
                api_url=settings.APPLICATION_PROCESSOR,
                handle=Handle.APPLICATION,
                data=payload
            )
        except Exception:
            logger.exception(f"Background task failed for task {task_id}")



# Global service instance
task_service = TaskService()