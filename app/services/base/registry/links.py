from uuid import UUID
from datetime import datetime


from fastapi import Request


from app.config import settings
from app.schemas.base.base_schemas import LinkHandle, LinkStatus
from app.services.base.registry.registry_interaction import interact_with_registry, make_meta, registry_make_search_params
from app.services.base.utils import Method, Timeout, get_project, get_account, get_user
from app.exceptions.main_exceptions import NotFoundException, DeletedException
from app.exceptions.sub_exceptions.not_found_exceptions import RegistryObjectDeactivatedException


__version__ = "1.0.0"



class LinksService:
    def __init__(self, base_registry_url: str = None):
        self.base_registry_url = base_registry_url or settings.SERVICE_REGISTRY_URL
        self.single_endpoint = LinkHandle.LINK
        self.plural_endpoint = LinkHandle.LINKS


    # Creates a new link between two objects
    # Input parameters:
    #   request: Request - FastAPI request object
    #   link_type: str - link type (for example, "author_book")
    #   object1: UUID - ID of the first object
    #   object2: UUID - ID of the second object
    #   link_code: str - unique link code (optional)
    #   weight: float - link weight from 0 to 1 (optional)
    #   direction: int - link direction 0-3 (optional)
    #   data: dict - arbitrary link data (optional)
    #   meta: dict - link metadata (optional)
    #   project_id: UUID - project ID (optional)
    #   account_id: UUID - account ID (optional)
    #   user_id: UUID - user ID (optional)
    #   timeout: float | Timeout - operation timeout (Timeout.DEFAULT by default)
    # Output parameters:
    #   dict - created link object
    async def create(
        self,
        request: Request,
        link_type: str,
        object1: UUID,
        object2: UUID,
        link_code: str = None,
        weight: float = None,
        direction: int = None,
        data: dict = None,
        meta: dict = None,
        project_id: UUID = None,
        account_id: UUID = None,
        user_id: UUID = None,
        timeout: float | Timeout = Timeout.DEFAULT,
    ) -> dict:
        payload = {
            "link_type": link_type,
            "object1": str(object1),
            "object2": str(object2),
            "link_code": link_code,
            "project_id": get_project(project_id),
            "account_id": get_account(account_id),
            "user_id": get_user(user_id),
        }
        if link_code is not None:
            payload["link_code"] = link_code
        if weight is not None:
            payload["weight"] = weight
        if direction is not None:
            payload["direction"] = direction
        if data is not None:
            payload["data"] = data
        if meta is not None:
            payload["meta"] = meta


        return await interact_with_registry(
            request=request,
            method=Method.POST,
            registry_url=self.base_registry_url,
            registry_name=self.single_endpoint,
            data=payload,
            timeout=timeout,
        )


    # Retrieves a link by ID while checking its association with the project/account/user
    # Input parameters:
    #   request: Request - FastAPI request object
    #   link_id: UUID - link ID
    #   project_id: UUID - project ID (optional)
    #   account_id: UUID - account ID (optional)
    #   user_id: UUID - user ID (optional)
    #   check_account: bool - check association with the account (True by default)
    #   check_user: bool - check association with the user (True by default)
    #   active_records: bool - return only active records (True by default)
    #   timeout: float | Timeout - operation timeout (Timeout.DEFAULT by default)
    # Output parameters:
    #   dict - link object
    async def get(
        self,
        request: Request,
        link_id: UUID,
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
            _id=link_id,
            active_records=active_records,
            timeout=timeout,
        )


        if project_id is not None:
            if get_project(result.get("project_id")) != get_project(project_id):
                raise NotFoundException(f"Link with ID {link_id} not found")


        if check_account and get_account(result.get("account_id")) != get_account(account_id):
            raise NotFoundException(f"Link with ID {link_id} not found")


        if check_user and get_user(result.get("user_id")) != get_user(user_id):
            raise NotFoundException(f"Link with ID {link_id} not found")


        return result


    # Fully updates a link (PUT)
    # Input parameters:
    #   request: Request - FastAPI request object
    #   link_id: UUID - link ID
    #   data: dict - complete link data for updating
    #   project_id: UUID - project ID (optional)
    #   account_id: UUID - account ID (optional)
    #   user_id: UUID - user ID (optional)
    #   check_account: bool - check association with the account (True by default)
    #   check_user: bool - check association with the user (True by default)
    #   timeout: float | Timeout - operation timeout (Timeout.DEFAULT by default)
    # Output parameters:
    #   dict - updated link object
    async def update(
        self,
        request: Request,
        link_id: UUID,
        data: dict,
        project_id: UUID = None,
        account_id: UUID = None,
        user_id: UUID = None,
        check_account: bool = True,
        check_user: bool = True,
        timeout: float | Timeout = Timeout.DEFAULT,
    ) -> dict:
        await self.get(
            request=request,
            link_id=link_id,
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
            _id=link_id,
            data=data,
            timeout=timeout,
        )


    # Partially updates a link (PATCH)
    # Input parameters:
    #   request: Request - FastAPI request object
    #   link_id: UUID - link ID
    #   link_code: str - unique link code (optional)
    #   link_type: str - link type (optional)
    #   weight: float - link weight from 0 to 1 (optional)
    #   direction: int - link direction 0-3 (optional)
    #   data: dict - arbitrary data for updating (optional)
    #   meta: dict - metadata for updating (optional)
    #   project_id: UUID - project ID (optional)
    #   account_id: UUID - account ID (optional)
    #   user_id: UUID - user ID (optional)
    #   check_account: bool - check association with the account (True by default)
    #   check_user: bool - check association with the user (True by default)
    #   timeout: float | Timeout - operation timeout (Timeout.DEFAULT by default)
    # Output parameters:
    #   dict - updated link object
    async def patch(
        self,
        request: Request,
        link_id: UUID,
        link_code: str = None,
        link_type: str = None,
        weight: float = None,
        direction: int = None,
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
            link_id=link_id,
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
        if link_code is not None:
            patch_data["link_code"] = link_code
        if link_type is not None:
            patch_data["link_type"] = link_type
        if weight is not None:
            patch_data["weight"] = weight
        if direction is not None:
            patch_data["direction"] = direction


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
            _id=link_id,
            data=patch_data,
            timeout=timeout,
        )



    # Deactivates a link (soft delete)
    # Input parameters:
    #   request: Request - FastAPI request object
    #   link_id: UUID - link ID
    #   project_id: UUID - project ID (optional)
    #   account_id: UUID - account ID (optional)
    #   user_id: UUID - user ID (optional)
    #   check_account: bool - check association with the account (True by default)
    #   check_user: bool - check association with the user (True by default)
    #   change_code: bool - replace link_code with "old_code:id" (True by default)
    #   timeout: float | Timeout - operation timeout (Timeout.DEFAULT by default)
    # Output parameters:
    #   dict - link object with updated status
    async def delete(
        self,
        request: Request,
        link_id: UUID,
        project_id: UUID = None,
        account_id: UUID = None,
        user_id: UUID = None,
        check_account: bool = True,
        check_user: bool = True,
        change_code: bool = True,
        timeout: float | Timeout = Timeout.DEFAULT,
    ) -> dict:
        return await self.set_status(
            request, link_id, LinkStatus.HIDDEN,
            project_id, account_id, user_id,
            check_account, check_user, timeout,
            change_code=change_code,
        )


    # Sets the link status
    # Input parameters:
    #   request: Request - FastAPI request object
    #   link_id: UUID - link ID
    #   status: str - new status ("active" or "inactive")
    #   project_id: UUID - project ID (optional)
    #   account_id: UUID - account ID (optional)
    #   user_id: UUID - user ID (optional)
    #   check_account: bool - check association with the account (True by default)
    #   check_user: bool - check association with the user (True by default)
    #   timeout: float | Timeout - operation timeout (Timeout.DEFAULT by default)
    #   change_code: bool - change link_code when changing the status:
    #                       - when deactivating: adds ":id" to link_code
    #                       - when activating: removes ":id" from the end of link_code
    # Output parameters:
    #   dict - link object with updated status
    # Exceptions:
    #   DeletedException - if the link has already been deleted
    async def set_status(
        self,
        request: Request,
        link_id: UUID,
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
            link_id=link_id,
            project_id=project_id,
            account_id=account_id,
            user_id=user_id,
            check_account=check_account,
            check_user=check_user,
            active_records=False,
            timeout=timeout,
        )


        # If the link already has the required status
        current_status = current.get("meta", {}).get("status")
        if current_status == status:
            if status == LinkStatus.HIDDEN:
                raise DeletedException()
            return current


        updated_meta = make_meta(existing_meta=current.get("meta"), status=status)
        patch_data = {"meta": updated_meta}


        # Change link_code when deactivating
        if change_code and status == LinkStatus.HIDDEN:
            old_code = current.get("link_code")
            new_code = f"{old_code}:{link_id}" if old_code else str(link_id)
            patch_data["link_code"] = new_code


        # Restore link_code when activating
        if change_code and status == LinkStatus.ACTIVE:
            old_code = current.get("link_code", "")
            parts = old_code.rsplit(":", 1)
            if len(parts) == 2 and parts[1] == str(link_id):
                patch_data["link_code"] = parts[0]
            else:
                patch_data["link_code"] = old_code


        try:
            return await interact_with_registry(
                request=request,
                method=Method.PATCH,
                registry_url=self.base_registry_url,
                registry_name=self.single_endpoint,
                _id=link_id,
                data=patch_data,
                timeout=timeout,
            )
        except RegistryObjectDeactivatedException:
            # If the update attempt reveals that the link has been deleted
            raise DeletedException()


    # Sets the link's bit flags
    # Input parameters:
    #   request: Request - FastAPI request object
    #   link_id: UUID - link ID
    #   flags: int - new flags value
    #   project_id: UUID - project ID (optional)
    #   account_id: UUID - account ID (optional)
    #   user_id: UUID - user ID (optional)
    #   check_account: bool - check association with the account (True by default)
    #   check_user: bool - check association with the user (True by default)
    #   timeout: float | Timeout - operation timeout (Timeout.DEFAULT by default)
    # Output parameters:
    #   dict - link object with updated flags
    async def set_flags(
        self,
        request: Request,
        link_id: UUID,
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
            link_id=link_id,
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
            link_id=link_id,
            meta=updated_meta,
            project_id=project_id,
            account_id=account_id,
            user_id=user_id,
            check_account=check_account,
            check_user=check_user,
            timeout=timeout,
        )


    # Activates a link (sets the status to "active")
    # Input parameters:
    #   request: Request - FastAPI request object
    #   link_id: UUID - link ID
    #   project_id: UUID - project ID (optional)
    #   account_id: UUID - account ID (optional)
    #   user_id: UUID - user ID (optional)
    #   check_account: bool - check association with the account (True by default)
    #   check_user: bool - check association with the user (True by default)
    #   restore_code: bool - restore link_code (remove ":id" from the end) (True by default)
    #   timeout: float | Timeout - operation timeout (Timeout.DEFAULT by default)
    # Output parameters:
    #   dict - link object with updated status
    async def activate(
        self,
        request: Request,
        link_id: UUID,
        project_id: UUID = None,
        account_id: UUID = None,
        user_id: UUID = None,
        check_account: bool = True,
        check_user: bool = True,
        restore_code: bool = True,
        timeout: float | Timeout = Timeout.DEFAULT,
    ) -> dict:
        return await self.set_status(
            request, link_id, LinkStatus.ACTIVE,
            project_id, account_id, user_id,
            check_account, check_user, timeout,
            change_code=restore_code,
        )



    # Retrieves a list of links with filtering, pagination, sorting, and date filtering
    # Input parameters:
    #   request: Request - FastAPI request object
    #   project_id: UUID - project ID (optional)
    #   account_id: UUID - account ID (optional)
    #   user_id: UUID - user ID (optional)
    #   ids: list[UUID] - list of link IDs to filter by (optional)
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
    async def links(
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



    # Checks whether a link exists and returns its ID
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
    #   UUID | None - ID of the found link if it exists; otherwise, None
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


        response = await self.links(
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


    # Checks whether a link exists
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
    #   bool - True if at least one link is found; otherwise, False
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


    # Returns the number of links matching the filters
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
    #   int - number of links matching the filters
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
        response = await self.links(
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


    # Bulk creation of links
    # Input parameters:
    #   request: Request - FastAPI request object
    #   links: list[dict] - array of link objects to create
    #   project_id: UUID - project ID (optional)
    #   account_id: UUID - account ID (optional)
    #   user_id: UUID - user ID (optional)
    #   timeout: float | Timeout - operation timeout (Timeout.LONG by default)
    # Output parameters:
    #   list[dict] - array of created link objects
    async def bulk_create(
        self,
        request: Request,
        links: list[dict],
        project_id: UUID = None,
        account_id: UUID = None,
        user_id: UUID = None,
        timeout: float | Timeout = Timeout.LONG,
    ) -> list[dict]:
        processed_links = []
        for link in links:
            link["project_id"] = get_project(link.get("project_id", project_id))
            link["account_id"] = get_account(link.get("account_id", account_id))
            link["user_id"] = get_user(link.get("user_id", user_id))
            processed_links.append(link)


        return await interact_with_registry(
            request=request,
            method=Method.POST,
            registry_url=self.base_registry_url,
            registry_name=self.plural_endpoint,
            data=processed_links,
            timeout=timeout,
        )


    # Bulk update of links (PUT)
    # Input parameters:
    #   request: Request - FastAPI request object
    #   links: list[dict] - array of link objects for full update
    #   timeout: float | Timeout - operation timeout (Timeout.LONG by default)
    # Output parameters:
    #   list[dict] - array of updated link objects
    async def bulk_update(
        self,
        request: Request,
        links: list[dict],
        timeout: float | Timeout = Timeout.LONG,
    ) -> list[dict]:
        return await interact_with_registry(
            request=request,
            method=Method.PUT,
            registry_url=self.base_registry_url,
            registry_name=self.plural_endpoint,
            data=links,
            timeout=timeout,
        )


    # Bulk partial update of links (PATCH)
    # Input parameters:
    #   request: Request - FastAPI request object
    #   links: list[dict] - array of link objects for partial update
    #   timeout: float | Timeout - operation timeout (Timeout.LONG by default)
    # Output parameters:
    #   list[dict] - array of updated link objects
    async def bulk_patch(
        self,
        request: Request,
        links: list[dict],
        timeout: float | Timeout = Timeout.LONG,
    ) -> list[dict]:
        return await interact_with_registry(
            request=request,
            method=Method.PATCH,
            registry_url=self.base_registry_url,
            registry_name=self.plural_endpoint,
            data=links,
            timeout=timeout,
        )


    # Bulk deletion of links
    # Input parameters:
    #   request: Request - FastAPI request object
    #   link_ids: list[UUID] - array of link IDs to delete
    #   timeout: float | Timeout - operation timeout (Timeout.LONG by default)
    # Output parameters:
    #   dict - API response with the operation result
    async def bulk_delete(
        self,
        request: Request,
        link_ids: list[UUID],
        timeout: float | Timeout = Timeout.LONG,
    ) -> dict:
        params = {"id": ",".join(str(id_) for id_ in link_ids)}
        return await interact_with_registry(
            request=request,
            method=Method.DELETE,
            registry_url=self.base_registry_url,
            registry_name=self.plural_endpoint,
            params=params,
            timeout=timeout,
        )


    # Creates or updates a link by a unique field
    # Input parameters:
    #   request: Request - FastAPI request object
    #   unique_field: str - name of the unique field (for example, "link_code")
    #   unique_value: str - value of the unique field
    #   link_type: str - link type (optional)
    #   object1: UUID - ID of the first object (optional)
    #   object2: UUID - ID of the second object (optional)
    #   link_code: str - unique link code (optional)
    #   weight: float - link weight (optional)
    #   direction: int - link direction (optional)
    #   data: dict - arbitrary link data (optional)
    #   meta: dict - link metadata (optional)
    #   project_id: UUID - project ID (optional)
    #   account_id: UUID - account ID (optional)
    #   user_id: UUID - user ID (optional)
    #   check_account: bool - check association with the account (True by default)
    #   check_user: bool - check association with the user (True by default)
    #   timeout: float | Timeout - operation timeout (Timeout.DEFAULT by default)
    # Output parameters:
    #   dict - created or updated link object
    async def upsert(
        self,
        request: Request,
        unique_field: str,
        unique_value: str,
        link_type: str = None,
        object1: UUID = None,
        object2: UUID = None,
        link_code: str = None,
        weight: float = None,
        direction: int = None,
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
            if link_type is not None:
                update_data["link_type"] = link_type
            if object1 is not None:
                update_data["object1"] = str(object1)
            if object2 is not None:
                update_data["object2"] = str(object2)
            if link_code is not None:
                update_data["link_code"] = link_code
            if weight is not None:
                update_data["weight"] = weight
            if direction is not None:
                update_data["direction"] = direction
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
                link_id=existing_id,
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
                link_type=link_type,
                object1=object1,
                object2=object2,
                link_code=link_code,
                weight=weight,
                direction=direction,
                data=data,
                meta=meta,
                project_id=project_id,
                account_id=account_id,
                user_id=user_id,
                timeout=timeout,
            )
