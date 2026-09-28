"""
Authentication system utilities
"""
from typing import Dict, Set, Optional
from token_sub_info.get_info import get_all_info
from token_sub_info.utils import get_token_from_request

from app.config import settings

from .schema import AuthConfig, UserAuthInfo, AccessLevel, DebugMode


#   #   Getting access key in the format we need
def get_public_key() -> bytes:
    return settings.ACCESS_TOKEN_PUBLIC_KEY.replace("\\n", "\n").encode()


#   Check whether access is forbidden according to general environment rules
def _is_access_denied(auth_config: AuthConfig, access_level: Optional[AccessLevel]) -> bool:
    # Case 1: Method is explicitely forbidden
    if access_level == AccessLevel.BLOCKED:
        return True

    # Case 2: Prod mode is active and method is not configured - block access
    if auth_config.debug_mode == DebugMode.PROD and access_level is None:
        return True

    # All other cases are check further on, including case 3: Dev mode is on and method is not configure - grant access
    return False


#   Gets complete user permissions info
def get_user_auth_info(token: str) -> UserAuthInfo:
    #   Get data from token
    user_data = get_all_info(token, get_public_key(), settings.JWT_ALGORITHM)

    # Get user explicit permissions
    user_permissions = get_user_permissions(user_data)

    # Get user groups
    user_groups = get_user_groups(user_data)

    # Collect all user permissions (explicit + group)
    # Group permissions are a copy of user permissions for now
    all_permissions = user_permissions.copy()


    # Get project token has been issued for
    user_product = get_user_project(user_data)

    return UserAuthInfo(
        user_permissions=user_permissions,
        groups=user_groups,
        all_permissions=all_permissions,
        project_id=user_product
    )


#   User permissions in current service
def get_user_permissions(token_data: dict):
    user_permissions = token_data.get("permissions")
    explicit_permissions = get_service_data(user_permissions)
    return explicit_permissions


#   Service access groups
def get_user_groups(token_data: dict):
    groups = token_data.get("groups")
    explicit_groups = get_service_data(groups)
    return explicit_groups


#   The project permissions have been issued for
def get_user_project(token_data: dict):
    return token_data.get("project_id")


#   Utility to transform permissions/groups into a set
def get_service_data(all_data):
    explicit_data = set()
    if all_data and settings.SERVICE_NAME in all_data:
        service_data = all_data[settings.SERVICE_NAME]
        if isinstance(service_data, list):
            explicit_data = set(service_data)
        elif isinstance(service_data, dict):
            explicit_data = set(service_data.keys())

    return explicit_data


#   Get all user permissions for the current service
def get_all_permissions(auth_config: AuthConfig, user_auth_info: UserAuthInfo) -> UserAuthInfo:
    _permissions = set(user_auth_info.user_permissions)
    for group_name in user_auth_info.groups:
        _permissions = _permissions.union(set(auth_config.groups[group_name]))

    return UserAuthInfo(
        user_permissions=user_auth_info.user_permissions,
        groups=user_auth_info.groups,
        all_permissions=_permissions
    )


#   Personal and group permissions in service
def get_user_service_info(request) -> UserAuthInfo:
    # Need config with permissions and group settings
    auth_config: AuthConfig = request.app.state.auth_config

    token = get_token_from_request(request)
    user_auth_info = get_user_auth_info(token)
    return get_all_permissions(auth_config, user_auth_info)


#   Checks whether the user has permission to execute function
def _has_permission(user_auth_info: UserAuthInfo, permission_name: str, auth_config: AuthConfig) -> bool:
    if not permission_name:
        return False

    method_code = permission_name.lower()

    # PRIORITY 1: Check explicit user permissions
    if method_code in user_auth_info.user_permissions:
        return True

    # PRIORITY 2: Check group permissions
    for group_name in user_auth_info.groups:
        if group_name in auth_config.groups and method_code in auth_config.groups[group_name]:
            return True

    return False


#   Return current permissions configuration info
def get_lib_info(auth_config: AuthConfig) -> dict:
    result = {
        "auth_enabled": settings.AUTH_ENABLED,
        "debug_mode": auth_config.debug_mode.value,
        "environment": settings.ENVIRONMENT,
        "permissions": {
            function_name: level.value
            for function_name, level in auth_config.permissions.items()
        },
        "groups": {
            group_name: list(function_names)
            for group_name, function_names in auth_config.groups.items()
        }
    }
    return result


#   Return function access level (for debugging)
def get_function_access_level(auth_config: AuthConfig, function_name: str) -> str:
    access_level = auth_config.permissions.get(function_name)

    if access_level:
        return access_level.value
    elif auth_config.debug_mode == DebugMode.DEV:
        return "OPEN (DEV mode default)"
    else:
        return "DENIED (PROD mode default)"
