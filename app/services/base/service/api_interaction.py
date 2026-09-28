from json import JSONDecodeError
from typing import Tuple

from fastapi import Request, status
from fastapi.encoders import jsonable_encoder

from app.exceptions.main_exceptions import ServiceException
from app.exceptions.sub_exceptions.failed_dependency_exceptions import IncorrectFormatInServiceException, \
    ServiceInteractionException
from app.exceptions.sub_exceptions.internal_exceptions import InvalidMethodException
from app.services.base.utils import Method, HeaderAlias
from app.libs.nestorlog import nestor


async def interact_with_api(
        request: Request,
        method: Method,
        api_url: str,
        handle: str,
        headers: dict | None = None,
        params: dict | list | None = None,
        data: dict | None = None
) -> Tuple[dict, int]:
    url = api_url + handle

    if headers and not headers.get(HeaderAlias.AUTHORIZATION):
        headers[HeaderAlias.AUTHORIZATION] = request.headers.get(HeaderAlias.AUTHORIZATION)
    elif not headers:
        headers = {}
        if request.headers.get(HeaderAlias.AUTHORIZATION):
            headers[HeaderAlias.AUTHORIZATION] = request.headers.get(HeaderAlias.AUTHORIZATION)
        if request.headers.get(HeaderAlias.PROJECT_ID):
            headers[HeaderAlias.PROJECT_ID] = request.headers.get(HeaderAlias.PROJECT_ID)
    # Attach current session id to request. Only accepted by services that support session_context
    client = request.app.requests_client

    try:
        match method:
            case Method.GET:
                response = await client.get(url, params=jsonable_encoder(params), headers=jsonable_encoder(headers))
                nestor.info(f"GET {url}, params: {params}", name='interact_with_api')
            case Method.POST:
                response = await client.post(url, json=jsonable_encoder(data), headers=jsonable_encoder(headers))
                nestor.info(f"POST {url}, params: {params}, data: {data}.", name='interact_with_api')
            case Method.PATCH:
                response = await client.patch(url, json=jsonable_encoder(data), headers=jsonable_encoder(headers))
                nestor.info(f"PATCH {url}, data: {data}", name='interact_with_api')
            case Method.DELETE:
                response = await client.delete(url, headers=jsonable_encoder(headers), json=jsonable_encoder(data))
                nestor.info(f"DELETE {url}", name='interact_with_api')
            case _:
                raise InvalidMethodException
    except InvalidMethodException:
        raise InvalidMethodException
    except Exception as e:
        nestor.error(f"Ошибка в методе interact_with_api, сервис {api_url} вернул ошибку.", name='service_error')
        error = f"{e.get("detail") if isinstance(e, dict) and "detail" in e else str(e)}"
        raise ServiceInteractionException(service_error=error)
    try:
        response_status_code = response.status_code
        if response_status_code == status.HTTP_204_NO_CONTENT:
            response_info = None
        else:
            response_info = response.json()
    except JSONDecodeError as e:
        nestor.error(f"Failed to decode json: {e}.", name='json_decode_error')
        raise IncorrectFormatInServiceException

    nestor.info(f"interact_with_api response data: {response_info}.", name='interact_with_api')

    if response.status_code not in (status.HTTP_200_OK, status.HTTP_201_CREATED, status.HTTP_204_NO_CONTENT):
        if response_info and response_info.get('detail'):
            if type(response_info.get('detail')) is dict and response_info.get('detail').get('code') \
                and response_info.get('detail').get('message'):
                code = response_info.get('detail').get('code')
                message = response_info.get('detail').get('message')
                raise ServiceException(status_code=response.status_code, code=code, message=message)
        nestor.error(f"Ошибка в методе interact_with_api, сервис {api_url} вернул ошибку", name='service_error')
        raise ServiceInteractionException(service_error=f"{response, response_info}")

    return response_info, response_status_code
