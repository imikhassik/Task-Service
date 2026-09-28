from datetime import datetime
from uuid import UUID

from fastapi import Request, status
from fastapi.encoders import jsonable_encoder

from app.libs.date import get_midnight
from app.libs.nestorlog import nestor

from app.exceptions.main_exceptions import NotFoundException
from app.exceptions.sub_exceptions.bad_request_exceptions import EntityExistsException
from app.exceptions.sub_exceptions.failed_dependency_exceptions import RegistryInteractionException, IncorrectFormatInRegistryException
from app.exceptions.sub_exceptions.not_found_exceptions import RegistryObjectDeactivatedException

from app.schemas.base.base_schemas import RegistryObject, LinkObject, RegistryObjectStatus

from app.services.base.utils import Method, Timeout


__version__ = "1.0.1"


async def interact_with_registry(
    request: Request,
    method: Method,
    registry_url: str,
    registry_name: str,
    _id: UUID = None,
    params: dict = None,
    data: RegistryObject | LinkObject | list | dict = None,
    active_records: bool = True,
    raise_not_found: bool = True,
    timeout: float | Timeout = Timeout.DEFAULT,
) -> dict | list[dict]:
    if _id is None:
        full_url = f"{registry_url}/{registry_name}/"
    else:
        full_url = f"{registry_url}/{registry_name}/{_id}/"

    serialized_data = jsonable_encoder(data) if data is not None else None
    nestor.debug(f"Request to {full_url}: method={method}, params={params}, data={serialized_data}")

    headers = {}
    if "X-Session-ID" in request.headers:
        headers["X-Session-ID"] = request.headers["X-Session-ID"]

    timeout_sec = float(timeout)
    client = request.app.requests_client

    try:
        match method:
            case Method.GET:
                response = await client.get(full_url, params=params, timeout=timeout_sec, headers=headers)
            case Method.POST:
                response = await client.post(full_url, json=serialized_data, timeout=timeout_sec, headers=headers)
            case Method.PUT:
                response = await client.put(full_url, json=serialized_data, timeout=timeout_sec, headers=headers)
            case Method.PATCH:
                response = await client.patch(full_url, json=serialized_data, timeout=timeout_sec, headers=headers)
            case Method.DELETE:
                response = await client.delete(full_url, timeout=timeout_sec, headers=headers)
    except Exception as e:
        nestor.error(f"Registry request failed: {full_url}, error={e}")
        raise RegistryInteractionException(registry_error=str(e))

    try:
        response_data = response.json()
    except Exception as e: # NOQA: F841
        nestor.error(f"Failed to parse registry response: {full_url}, response={response.text}")
        raise IncorrectFormatInRegistryException

    #   Object not found (404 or empty response)
    if raise_not_found and (response.status_code == status.HTTP_404_NOT_FOUND or not response_data):
        raise NotFoundException

    if response.status_code == status.HTTP_400_BAD_REQUEST and 'exists' in str(response_data):
        raise EntityExistsException

    if response.status_code not in (status.HTTP_200_OK, status.HTTP_201_CREATED):
        raise RegistryInteractionException(registry_error=str(response_data))

    if active_records and isinstance(response_data, dict) and "meta" in response_data:
        meta = response_data.get("meta", {})
        if isinstance(meta, dict) and meta.get("status") == RegistryObjectStatus.HIDDEN:
            raise RegistryObjectDeactivatedException

    return response_data


def make_meta(
    existing_meta: dict = None,
    status: str = None,
    flags: int = None,
    internal_id: int = None,
    key_version: str = None,
) -> dict:
    meta = existing_meta.copy() if existing_meta else {}
    if status is not None:
        meta["status"] = status
    if flags is not None:
        meta["flags"] = flags
    if internal_id is not None:
        meta["internal_id"] = internal_id
    if key_version is not None:
        meta["key_version"] = key_version
    return meta


def registry_check_search_params(
    modified_after: datetime = None,
    modified_before: datetime = None,
    sort_by: str = None,
    order_by: str = None,
) -> bool:
    return bool(modified_after or modified_before or sort_by or order_by)


def registry_make_datetime_range(
    params: dict,
    field_name: str,
    after: datetime = None,
    before: datetime = None,
) -> dict:
    if after:
        params[f"{field_name}__gt"] = get_midnight(after, -1)
    if before:
        params[f"{field_name}__lt"] = get_midnight(before, 1)
    return params


def registry_make_search_params(
    params: dict,
    modified_after: datetime = None,
    modified_before: datetime = None,
    created_after: datetime = None,
    created_before: datetime = None,
    sort_by: str = None,
    order_by: str = None,
    **custom_ranges,
) -> dict:
    if modified_after or modified_before:
        params = registry_make_datetime_range(params, "modified_date", after=modified_after, before=modified_before)
    if created_after or created_before:
        params = registry_make_datetime_range(params, "created_date", after=created_after, before=created_before)
    for key, value in custom_ranges.items():
        if key.endswith("_after"):
            field = key[:-6]
            params = registry_make_datetime_range(params, field, after=value)
        elif key.endswith("_before"):
            field = key[:-7]
            params = registry_make_datetime_range(params, field, before=value)
    if sort_by:
        order = "-" if order_by == "desc" else ""
        params["ordering"] = f"{order}{sort_by}"
    return params