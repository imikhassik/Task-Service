from uuid import UUID
from datetime import datetime


from fastapi import Request


from app.config import settings
from app.schemas.base.base_schemas import ItemStatus
from app.services.base.registry.registry_interaction import interact_with_registry, make_meta, registry_make_search_params
from app.services.base.utils import Method, Timeout, get_project, get_account, get_user
from app.exceptions.main_exceptions import NotFoundException, DeletedException
from app.exceptions.sub_exceptions.not_found_exceptions import RegistryObjectDeactivatedException


__version__ = "1.0.0"



class ItemsService:
    def __init__(
        self,
        single_name: str,
        plural_name: str,
        base_registry_url: str = None,
    ):
        self.base_registry_url = base_registry_url or settings.SERVICE_REGISTRY_URL
        self.single_endpoint = single_name
        self.plural_endpoint = plural_name


    # Creates a new object in the registry
    # Input parameters:
    #   request: Request - FastAPI request object
    #   object_id: UUID - object ID (optional; generated if not specified)
    #   object_type: str - object type (for example, "book", "person")
    #   object_code: str - unique object code (optional)
    #   object_item: UUID - parent object ID (optional)
    #   data: dict - arbitrary object data (optional)
    #   meta: dict - object metadata (optional)
    #   project_id: UUID - project ID (optional)
    #   account_id: UUID - account ID (optional)
    #   user_id: UUID - user ID (optional)
    #   timeout: float | Timeout - operation timeout (Timeout.DEFAULT by default)
    # Output parameters:
    #   dict - created object
    async def create(
        self,
        request: Request,
        object_id: UUID = None,
        object_type: str = None,
        object_code: str = None,
        object_item: UUID = None,
        data: dict = None,
        meta: dict = None,
        project_id: UUID = None,
        account_id: UUID = None,
        user_id: UUID = None,
        timeout: float | Timeout = Timeout.DEFAULT,
    ) -> dict:
        payload = {}
        if object_id is not None:
            payload["id"] = str(object_id)
        if object_type is not None:
            payload["object_type"] = object_type
        if object_code is not None:
            payload["object_code"] = object_code
        if object_item is not None:
            payload["object_item"] = str(object_item)
        if data is not None:
            payload["data"] = data
        if meta is not None:
            payload["meta"] = meta


        # Always use DEFAULT when explicit values are not provided
        payload["project_id"] = get_project(project_id)
        payload["account_id"] = get_account(account_id)
        payload["user_id"] = get_user(user_id)


        return await interact_with_registry(
            request=request,
            method=Method.POST,
            registry_url=self.base_registry_url,
            registry_name=self.single_endpoint,
            data=payload,
            timeout=timeout,
        )


    # Retrieves an object by ID while checking its association with the project/account/user
    # Input parameters:
    #   request: Request - FastAPI request object
    #   object_id: UUID - object ID
    #   project_id: UUID - project ID (optional)
    #   account_id: UUID - account ID (optional)
    #   user_id: UUID - user ID (optional)
    #   check_account: bool - check association with the account (True by default)
    #   check_user: bool - check association with the user (True by default)
    #   active_records: bool - return only active records (True by default)
    #   timeout: float | Timeout - operation timeout (Timeout.DEFAULT by default)
    # Output parameters:
    #   dict - object
    async def get(
        self,
        request: Request,
        object_id: UUID,
        project_id: UUID = None,
        account_id: UUID = None,
        user_id: UUID = None,
        check_account: bool = True,
        check_user: bool = True,
        active_records: bool = True,
        timeout: float | Timeout = Timeout.DEFAULT,
    ) -> dict:
        result = await interact_with_registry(
            request=request,
            method=Method.GET,
            registry_url=self.base_registry_url,
            registry_name=self.single_endpoint,
            _id=object_id,
            active_records=active_records,
            timeout=timeout,
        )


        # Check project_id
        if project_id is not None:
            if get_project(result.get("project_id")) != get_project(project_id):
                raise NotFoundException(f"Object with ID {object_id} not found")


        # Check account_id
        if check_account and get_account(result.get("account_id")) != get_account(account_id):
            raise NotFoundException(f"Object with ID {object_id} not found")


        # Check user_id
        if check_user and get_user(result.get("user_id")) != get_user(user_id):
            raise NotFoundException(f"Object with ID {object_id} not found")


        return result


    # Fully updates an object (PUT)
    # Input parameters:
    #   request: Request - FastAPI request object
    #   object_id: UUID - object ID
    #   data: dict - complete object data for updating
    #   project_id: UUID - project ID (optional)
    #   account_id: UUID - account ID (optional)
    #   user_id: UUID - user ID (optional)
    #   check_account: bool - check association with the account (True by default)
    #   check_user: bool - check association with the user (True by default)
    #   timeout: float | Timeout - operation timeout (Timeout.DEFAULT by default)
    # Output parameters:
    #   dict - updated object
    async def update(
        self,
        request: Request,
        object_id: UUID,
        data: dict,
        project_id: UUID = None,
        account_id: UUID = None,
        user_id: UUID = None,
        check_account: bool = True,
        check_user: bool = True,
        timeout: float | Timeout = Timeout.DEFAULT,
    ) -> dict:
        # Check existence and access rights through get
        await self.get(
            request=request,
            object_id=object_id,
            project_id=project_id,
            account_id=account_id,
            user_id=user_id,
            check_account=check_account,
            check_user=check_user,
            active_records=True,
            timeout=timeout,
        )


        return await interact_with_registry(
            request=request,
            method=Method.PUT,
            registry_url=self.base_registry_url,
            registry_name=self.single_endpoint,
            _id=object_id,
            data=data,
            timeout=timeout,
        )


    # Partially updates an object (PATCH)
    # Input parameters:
    #   request: Request - FastAPI request object
    #   object_id: UUID - object ID
    #   object_code: str - unique object code (optional)
    #   object_type: str - object type (optional)
    #   object_item: UUID - parent object ID (optional)
    #   data: dict - arbitrary data for updating (optional)
    #   meta: dict - metadata for updating (optional)
    #   project_id: UUID - project ID (optional)
    #   account_id: UUID - account ID (optional)
    #   user_id: UUID - user ID (optional)
    #   check_account: bool - check association with the account (True by default)
    #   check_user: bool - check association with the user (True by default)
    #   timeout: float | Timeout - operation timeout (Timeout.DEFAULT by default)
    # Output parameters:
    #   dict - updated object
    async def patch(
        self,
        request: Request,
        object_id: UUID,
        object_code: str = None,
        object_type: str = None,
        object_item: UUID = None,
        data: dict = None,
        meta: dict = None,
        project_id: UUID = None,
        account_id: UUID = None,
        user_id: UUID = None,
        check_account: bool = True,
        check_user: bool = True,
        timeout: float | Timeout = Timeout.DEFAULT,
    ) -> dict:
        # Check existence and access rights through get
        await self.get(
            request=request,
            object_id=object_id,
            project_id=project_id,
            account_id=account_id,
            user_id=user_id,
            check_account=check_account,
            check_user=check_user,
            active_records=True,
            timeout=timeout,
        )


        patch_data = {}


        # Top-level fields
        if object_code is not None:
            patch_data["object_code"] = object_code
        if object_type is not None:
            patch_data["object_type"] = object_type
        if object_item is not None:
            patch_data["object_item"] = str(object_item)


        # Nested fields
        if data is not None:
            patch_data["data"] = data
        if meta is not None:
            patch_data["meta"] = meta


        return await interact_with_registry(
            request=request,
            method=Method.PATCH,
            registry_url=self.base_registry_url,
            registry_name=self.single_endpoint,
            _id=object_id,
            data=patch_data,
            timeout=timeout,
        )



    # Deactivates an object (soft delete)
    # Input parameters:
    #   request: Request - FastAPI request object
    #   object_id: UUID - object ID
    #   project_id: UUID - project ID (optional)
    #   account_id: UUID - account ID (optional)
    #   user_id: UUID - user ID (optional)
    #   check_account: bool - check association with the account (True by default)
    #   check_user: bool - check association with the user (True by default)
    #   change_code: bool - replace object_code with "old_code:id" (True by default)
    #   timeout: float | Timeout - operation timeout (Timeout.DEFAULT by default)
    # Output parameters:
    #   dict - object with the updated status
    async def delete(
        self,
        request: Request,
        object_id: UUID,
        project_id: UUID = None,
        account_id: UUID = None,
        user_id: UUID = None,
        check_account: bool = True,
        check_user: bool = True,
        change_code: bool = True,
        timeout: float | Timeout = Timeout.DEFAULT,
    ) -> dict:
        return await self.set_status(
            request, object_id, ItemStatus.HIDDEN,
            project_id, account_id, user_id,
            check_account, check_user, timeout,
            change_code=change_code,
        )



    # Sets the object status
    # Input parameters:
    #   request: Request - FastAPI request object
    #   object_id: UUID - object ID
    #   status: str - new status ("active" or "inactive")
    #   project_id: UUID - project ID (optional)
    #   account_id: UUID - account ID (optional)
    #   user_id: UUID - user ID (optional)
    #   check_account: bool - check association with the account (True by default)
    #   check_user: bool - check association with the user (True by default)
    #   timeout: float | Timeout - operation timeout (Timeout.DEFAULT by default)
    #   change_code: bool - change object_code when changing the status:
    #                       - when deactivating: adds ":id" to object_code
    #                       - when activating: removes ":id" from the end of object_code
    # Output parameters:
    #   dict - object with the updated status
    # Exceptions:
    #   DeletedException - if the object has already been deleted
    async def set_status(
        self,
        request: Request,
        object_id: UUID,
        status: str,
        project_id: UUID = None,
        account_id: UUID = None,
        user_id: UUID = None,
        check_account: bool = True,
        check_user: bool = True,
        timeout: float | Timeout = Timeout.DEFAULT,
        change_code: bool = False,
    ) -> dict:
        current = await self.get(
            request=request,
            object_id=object_id,
            project_id=project_id,
            account_id=account_id,
            user_id=user_id,
            check_account=check_account,
            check_user=check_user,
            active_records=False,
            timeout=timeout,
        )


        # If the object already has the required status
        current_status = current.get("meta", {}).get("status")
        if current_status == status:
            if status == ItemStatus.HIDDEN:
                raise DeletedException()
            return current


        updated_meta = make_meta(existing_meta=current.get("meta"), status=status)
        patch_data = {"meta": updated_meta}


        # Change object_code when deactivating
        if change_code and status == ItemStatus.HIDDEN:
            old_code = current.get("object_code")
            new_code = f"{old_code}:{object_id}" if old_code else str(object_id)
            patch_data["object_code"] = new_code


        # Restore object_code when activating
        if change_code and status == ItemStatus.ACTIVE:
            old_code = current.get("object_code", "")
            parts = old_code.rsplit(":", 1)
            if len(parts) == 2 and parts[1] == str(object_id):
                patch_data["object_code"] = parts[0]
            else:
                patch_data["object_code"] = old_code


        try:
            return await interact_with_registry(
                request=request,
                method=Method.PATCH,
                registry_url=self.base_registry_url,
                registry_name=self.single_endpoint,
                _id=object_id,
                data=patch_data,
                timeout=timeout,
            )
        except RegistryObjectDeactivatedException:
            # If the update attempt reveals that the object has been deleted
            raise DeletedException()


    # Sets the object's bit flags
    # Input parameters:
    #   request: Request - FastAPI request object
    #   object_id: UUID - object ID
    #   flags: int - new flags value
    #   project_id: UUID - project ID (optional)
    #   account_id: UUID - account ID (optional)
    #   user_id: UUID - user ID (optional)
    #   check_account: bool - check association with the account (True by default)
    #   check_user: bool - check association with the user (True by default)
    #   timeout: float | Timeout - operation timeout (Timeout.DEFAULT by default)
    # Output parameters:
    #   dict - object with updated flags
    async def set_flags(
        self,
        request: Request,
        object_id: UUID,
        flags: int,
        project_id: UUID = None,
        account_id: UUID = None,
        user_id: UUID = None,
        check_account: bool = True,
        check_user: bool = True,
        timeout: float | Timeout = Timeout.DEFAULT,
    ) -> dict:
        current = await self.get(
            request=request,
            object_id=object_id,
            project_id=project_id,
            account_id=account_id,
            user_id=user_id,
            check_account=check_account,
            check_user=check_user,
            active_records=False,
            timeout=timeout,
        )
        updated_meta = make_meta(existing_meta=current.get("meta"), flags=flags)
        return await self.patch(
            request=request,
            object_id=object_id,
            meta=updated_meta,
            project_id=project_id,
            account_id=account_id,
            user_id=user_id,
            check_account=check_account,
            check_user=check_user,
            timeout=timeout,
        )


    # Activates an object (sets the status to "active")
    # Input parameters:
    #   request: Request - FastAPI request object
    #   object_id: UUID - object ID
    #   project_id: UUID - project ID (optional)
    #   account_id: UUID - account ID (optional)
    #   user_id: UUID - user ID (optional)
    #   check_account: bool - check association with the account (True by default)
    #   check_user: bool - check association with the user (True by default)
    #   restore_code: bool - restore object_code (remove ":id" from the end) (True by default)
    #   timeout: float | Timeout - operation timeout (Timeout.DEFAULT by default)
    # Output parameters:
    #   dict - object with the updated status
    async def activate(
        self,
        request: Request,
        object_id: UUID,
        project_id: UUID = None,
        account_id: UUID = None,
        user_id: UUID = None,
        check_account: bool = True,
        check_user: bool = True,
        restore_code: bool = True,
        timeout: float | Timeout = Timeout.DEFAULT,
    ) -> dict:
        return await self.set_status(
            request, object_id, ItemStatus.ACTIVE,
            project_id, account_id, user_id,
            check_account, check_user, timeout,
            change_code=restore_code,
        )



    # Retrieves a list of objects with filtering, pagination, sorting, and date filtering
    # Input parameters:
    #   request: Request - FastAPI request object
    #   project_id: UUID - project ID
    #   account_id: UUID - account ID (optional)
    #   user_id: UUID - user ID (optional)
    #   ids: list[UUID] - list of object IDs to filter by (optional)
    #   check_account: bool - if True, search for an exact account_id match,
    #                        if False, search for the provided account_id or DEFAULT_ACCOUNT
    #   check_user: bool - if True, add a user_id filter,
    #                     if False, do not add a user_id filter
    #   offset: int - number of records to skip (optional)
    #   limit: int - number of records to return (optional)
    #   sort_by: str - field for sorting (for example, "created_date", "data__title")
    #   order_by: str - sort direction ("asc" or "desc")
    #   modified_after: datetime - start of the modified_date range (optional)
    #   modified_before: datetime - end of the modified_date range (optional)
    #   created_after: datetime - start of the created_date range (optional)
    #   created_before: datetime - end of the created_date range (optional)
    #   active_records: bool - return only active records (True by default)
    #   timeout: float | Timeout - operation timeout (Timeout.MEDIUM by default)
    #   **filters: dict - arbitrary filtering parameters
    # Output parameters:
    #   dict - object with count (current count), total (total count),
    #          next, previous, results fields
    async def items(
        self,
        request: Request,
        project_id: UUID = None,
        account_id: UUID = None,
        user_id: UUID = None,
        ids: list[UUID] = None,
        check_account: bool = True,
        check_user: bool = True,
        offset: int = None,
        limit: int = None,
        sort_by: str = None,
        order_by: str = None,
        modified_after: datetime = None,
        modified_before: datetime = None,
        created_after: datetime = None,
        created_before: datetime = None,
        active_records: bool = True,
        timeout: float | Timeout = Timeout.MEDIUM,
        **filters,
    ) -> dict:
        params = {k: v for k, v in filters.items() if v is not None}


        # Filter by list of IDs
        if ids is not None:
            params["id"] = ",".join(str(id_) for id_ in ids)


        # Pagination
        if offset is not None:
            params["offset"] = offset
        if limit is not None:
            params["limit"] = limit


        # Sorting and dates
        params = registry_make_search_params(
            params,
            modified_after=modified_after,
            modified_before=modified_before,
            created_after=created_after,
            created_before=created_before,
            sort_by=sort_by,
            order_by=order_by,
        )


        # project_id
        params["project_id"] = get_project(project_id)


        # account_id
        if check_account:
            params["account_id"] = get_account(account_id)
        else:
            if account_id is not None:
                params["account_id"] = f"{account_id},{get_account(None)}"
            else:
                params["account_id"] = get_account(None)


        # user_id
        if check_user:
            params["user_id"] = get_user(user_id)


        result = await interact_with_registry(
            request=request,
            method=Method.GET,
            registry_url=self.base_registry_url,
            registry_name=self.plural_endpoint,
            params=params,
            active_records=active_records,
            timeout=timeout,
        )


        # Convert to a unified dictionary format
        if isinstance(result, list):
            return {
                "count": len(result),
                "total": len(result),
                "next": None,
                "previous": None,
                "results": result,
            }
        else:
            if "total" not in result:
                result["total"] = result.get("count", 0)
                result["count"] = len(result.get("results", []))
            return result


    # Checks whether an object exists and returns its ID
    # Input parameters:
    #   request: Request - FastAPI request object
    #   project_id: UUID - project ID (optional)
    #   account_id: UUID - account ID (optional)
    #   user_id: UUID - user ID (optional)
    #   check_account: bool - check association with the account (True by default)
    #   check_user: bool - check association with the user (True by default)
    #   timeout: float | Timeout - operation timeout (Timeout.FAST by default)
    #   **filters: dict - arbitrary filtering parameters
    # Output parameters:
    #   UUID | None - ID of the found object if it exists; otherwise, None
    async def exists_or_get_id(
        self,
        request: Request,
        project_id: UUID = None,
        account_id: UUID = None,
        user_id: UUID = None,
        check_account: bool = True,
        check_user: bool = True,
        timeout: float | Timeout = Timeout.FAST,
        **filters,
    ) -> UUID | None:
        params = {k: v for k, v in filters.items() if v is not None}
        params["limit"] = 1


        response = await self.items(
            request=request,
            project_id=project_id,
            account_id=account_id,
            user_id=user_id,
            check_account=check_account,
            check_user=check_user,
            active_records=True,
            timeout=timeout,
            **params,
        )


        results = response.get("results", [])
        if results:
            return results[0]["id"]
        return None


    # Checks whether an object exists
    # Input parameters:
    #   request: Request - FastAPI request object
    #   project_id: UUID - project ID (optional)
    #   account_id: UUID - account ID (optional)
    #   user_id: UUID - user ID (optional)
    #   check_account: bool - check association with the account (True by default)
    #   check_user: bool - check association with the user (True by default)
    #   timeout: float | Timeout - operation timeout (Timeout.FAST by default)
    #   **filters: dict - arbitrary filtering parameters
    # Output parameters:
    #   bool - True if at least one object is found; otherwise, False
    async def exists(
        self,
        request: Request,
        project_id: UUID = None,
        account_id: UUID = None,
        user_id: UUID = None,
        check_account: bool = True,
        check_user: bool = True,
        timeout: float | Timeout = Timeout.FAST,
        **filters,
    ) -> bool:
        result = await self.exists_or_get_id(
            request=request,
            project_id=project_id,
            account_id=account_id,
            user_id=user_id,
            check_account=check_account,
            check_user=check_user,
            timeout=timeout,
            **filters,
        )
        return result is not None


    # Returns the number of objects matching the filters
    # Input parameters:
    #   request: Request - FastAPI request object
    #   project_id: UUID - project ID (optional)
    #   account_id: UUID - account ID (optional)
    #   user_id: UUID - user ID (optional)
    #   check_account: bool - check association with the account (True by default)
    #   check_user: bool - check association with the user (True by default)
    #   timeout: float | Timeout - operation timeout (Timeout.MEDIUM by default)
    #   **filters: dict - arbitrary filtering parameters
    # Output parameters:
    #   int - number of objects matching the filters
    async def count(
        self,
        request: Request,
        project_id: UUID = None,
        account_id: UUID = None,
        user_id: UUID = None,
        check_account: bool = True,
        check_user: bool = True,
        timeout: float | Timeout = Timeout.MEDIUM,
        **filters,
    ) -> int:
        params = {k: v for k, v in filters.items() if v is not None}
        params["limit"] = 1
        response = await self.items(
            request=request,
            project_id=project_id,
            account_id=account_id,
            user_id=user_id,
            check_account=check_account,
            check_user=check_user,
            active_records=True,
            timeout=timeout,
            **params,
        )
        return response.get("count", 0)


    # Bulk creation of objects
    # Input parameters:
    #   request: Request - FastAPI request object
    #   objects: list[dict] - array of objects to create
    #   project_id: UUID - project ID (optional)
    #   account_id: UUID - account ID (optional)
    #   user_id: UUID - user ID (optional)
    #   timeout: float | Timeout - operation timeout (Timeout.LONG by default)
    # Output parameters:
    #   list[dict] - array of created objects
    async def bulk_create(
        self,
        request: Request,
        objects: list[dict],
        project_id: UUID = None,
        account_id: UUID = None,
        user_id: UUID = None,
        timeout: float | Timeout = Timeout.LONG,
    ) -> list[dict]:
        processed_objects = []
        for obj in objects:
            obj["project_id"] = get_project(obj.get("project_id", project_id))
            obj["account_id"] = get_account(obj.get("account_id", account_id))
            obj["user_id"] = get_user(obj.get("user_id", user_id))
            processed_objects.append(obj)


        return await interact_with_registry(
            request=request,
            method=Method.POST,
            registry_url=self.base_registry_url,
            registry_name=self.plural_endpoint,
            data=processed_objects,
            timeout=timeout,
        )


    # Bulk object update (PUT)
    # Input parameters:
    #   request: Request - FastAPI request object
    #   objects: list[dict] - array of objects for full update
    #   timeout: float | Timeout - operation timeout (Timeout.LONG by default)
    # Output parameters:
    #   list[dict] - array of updated objects
    async def bulk_update(
        self,
        request: Request,
        objects: list[dict],
        timeout: float | Timeout = Timeout.LONG,
    ) -> list[dict]:
        return await interact_with_registry(
            request=request,
            method=Method.PUT,
            registry_url=self.base_registry_url,
            registry_name=self.plural_endpoint,
            data=objects,
            timeout=timeout,
        )


    # Bulk partial update of objects (PATCH)
    # Input parameters:
    #   request: Request - FastAPI request object
    #   objects: list[dict] - array of objects for partial update
    #   timeout: float | Timeout - operation timeout (Timeout.LONG by default)
    # Output parameters:
    #   list[dict] - array of updated objects
    async def bulk_patch(
        self,
        request: Request,
        objects: list[dict],
        timeout: float | Timeout = Timeout.LONG,
    ) -> list[dict]:
        return await interact_with_registry(
            request=request,
            method=Method.PATCH,
            registry_url=self.base_registry_url,
            registry_name=self.plural_endpoint,
            data=objects,
            timeout=timeout,
        )


    # Bulk deletion of objects
    # Input parameters:
    #   request: Request - FastAPI request object
    #   object_ids: list[UUID] - array of object IDs to delete
    #   timeout: float | Timeout - operation timeout (Timeout.LONG by default)
    # Output parameters:
    #   dict - API response with the operation result
    async def bulk_delete(
        self,
        request: Request,
        object_ids: list[UUID],
        timeout: float | Timeout = Timeout.LONG,
    ) -> dict:
        params = {"id": ",".join(str(id_) for id_ in object_ids)}
        return await interact_with_registry(
            request=request,
            method=Method.DELETE,
            registry_url=self.base_registry_url,
            registry_name=self.plural_endpoint,
            params=params,
            timeout=timeout,
        )


    # Creates or updates an object by a unique field
    # Input parameters:
    #   request: Request - FastAPI request object
    #   unique_field: str - name of the unique field (for example, "object_code")
    #   unique_value: str | UUID - value of the unique field
    #   object_id: UUID - object ID (optional)
    #   object_type: str - object type (optional)
    #   object_code: str - unique object code (optional)
    #   object_item: UUID - parent object ID (optional)
    #   data: dict - arbitrary object data (optional)
    #   meta: dict - object metadata (optional)
    #   project_id: UUID - project ID (optional)
    #   account_id: UUID - account ID (optional)
    #   user_id: UUID - user ID (optional)
    #   check_account: bool - check association with the account (True by default)
    #   check_user: bool - check association with the user (True by default)
    #   timeout: float | Timeout - operation timeout (Timeout.DEFAULT by default)
    # Output parameters:
    #   dict - created or updated object
    async def upsert(
        self,
        request: Request,
        unique_field: str,
        unique_value: str | UUID,
        object_id: UUID = None,
        object_type: str = None,
        object_code: str = None,
        object_item: UUID = None,
        data: dict = None,
        meta: dict = None,
        project_id: UUID = None,
        account_id: UUID = None,
        user_id: UUID = None,
        check_account: bool = True,
        check_user: bool = True,
        timeout: float | Timeout = Timeout.DEFAULT,
    ) -> dict:
        existing_id = await self.exists_or_get_id(
            request=request,
            project_id=project_id,
            account_id=account_id,
            user_id=user_id,
            check_account=check_account,
            check_user=check_user,
            timeout=timeout,
            **{unique_field: unique_value},
        )


        if existing_id:
            update_data = {}
            if object_id is not None:
                update_data["id"] = str(object_id)
            if object_type is not None:
                update_data["object_type"] = object_type
            if object_code is not None:
                update_data["object_code"] = object_code
            if object_item is not None:
                update_data["object_item"] = str(object_item)
            if data is not None:
                update_data["data"] = data
            if meta is not None:
                update_data["meta"] = meta
            if project_id is not None:
                update_data["project_id"] = str(project_id)
            if account_id is not None:
                update_data["account_id"] = str(account_id)
            if user_id is not None:
                update_data["user_id"] = str(user_id)


            return await self.update(
                request=request,
                object_id=existing_id,
                data=update_data,
                project_id=project_id,
                account_id=account_id,
                user_id=user_id,
                check_account=check_account,
                check_user=check_user,
                timeout=timeout,
            )
        else:
            return await self.create(
                request=request,
                object_id=object_id,
                object_type=object_type,
                object_code=object_code,
                object_item=object_item,
                data=data,
                meta=meta,
                project_id=project_id,
                account_id=account_id,
                user_id=user_id,
                timeout=timeout,
            )
