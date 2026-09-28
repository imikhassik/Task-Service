"""
Permissions validation decorator
"""
from functools import wraps
from typing import Optional, Union, Callable

from starlette.requests import Request
from token_sub_info.utils import get_token_from_request, validate_token

from app.config import settings
from app.exceptions.main_exceptions import ForbiddenException

from .schema import AuthConfig, AccessLevel, DebugMode
from .utils import get_user_auth_info, _has_permission, _is_access_denied, get_public_key


#   Only done at the start-up
def validate_permissions(permission_code: Union[str, Callable] = None):
    #   Return empty decorator if validation is off
    if not settings.AUTH_ENABLED:
        def noop_decorator(func):
            return func
        return noop_decorator

    #   No parameters request processing: @validate_permissions
    if callable(permission_code):
        func = permission_code

        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            return await _check_access(func, None, request, *args, **kwargs)
        return wrapper

    #   Request processing with parameters: @validate_permissions("PERMISSION_CODE")
    def real_decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            return await _check_access(func, permission_code, request, *args, **kwargs)
        return wrapper

    return real_decorator


#   Check access in accordance with method configuration and user permissions
async def _check_access(func: Callable, permission_code: Optional[str], request: Request, *args, **kwargs):
    function_name = func.__name__
    auth_config: AuthConfig = request.app.state.auth_config

    #   If permission code is not specified, function name becomes the code
    if not permission_code:
        permission_code = function_name

    #   Get function permission level
    access_level = auth_config.permissions.get(permission_code.lower())

    #   Check access in accordance with DEV/PROD mode logic
    if _is_access_denied(auth_config, access_level):
        raise ForbiddenException

    #   In dev mode absent permissions mean that the method is open
    if access_level is None and auth_config.debug_mode == DebugMode.DEV:
        access_level = AccessLevel.OPEN

    #   Get token (can be None for OPEN methods)
    if access_level != AccessLevel.OPEN:
        token = get_token_from_request(request)
        if not token:
            raise ForbiddenException

        #   Need user permissions (specified explicitely or via group permissions)
        user_auth_info = get_user_auth_info(token)

        #   Someone is trying to use token receive for a different project
        if user_auth_info.project_id and user_auth_info.project_id != request.headers.get('project-id'):
            raise ForbiddenException

    if access_level == AccessLevel.OPEN:
        #   Access openn - no check necessary
        pass

    elif access_level == AccessLevel.AUTHORIZED:
        #   Authorization required
        validate_token(token, get_public_key(), settings.JWT_ALGORITHM)

    elif access_level == AccessLevel.GRANTED:
        if not _has_permission(user_auth_info, permission_code, auth_config):
            raise ForbiddenException

    else:
        #   Weird access level. Just in case although not likely
        print(f"Unknown level {access_level}")
        raise ForbiddenException

    #   Call the original function
    return await func(request, *args, **kwargs)
