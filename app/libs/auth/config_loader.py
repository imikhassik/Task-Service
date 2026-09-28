"""
Authentication configuration loading and parsing
"""
import os
from pathlib import Path
from typing import Dict, Set
import yaml

from fastapi import FastAPI

from app.config import settings
from .schema import AuthConfig, DebugMode, AccessLevel


#   .auth.yaml config parsing
def parse_auth() -> AuthConfig:
    file_path = Path(settings.AUTH_PATH)

    #   There must be a config file in prod
    if not file_path.exists():
        if settings.ENVIRONMENT == DebugMode.PROD:
            raise FileNotFoundError(
                f"Auth configuration file not found in {settings.ENVIRONMENT} mode: {settings.AUTH_PATH}.\n"
                f"Service cannot start without security configuration."
            )
        else:
            print(f"WARNING: Auth file not found at {settings.AUTH_PATH}. Using default settings.")
            return AuthConfig(
                debug_mode=DebugMode.PROD,
                permissions={},
                groups={}
            )

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        if settings.ENVIRONMENT == DebugMode.PROD:
            raise ValueError(f"Invalid YAML format in auth config: {e}")
        else:
            print(f"WARNING: Invalid auth config, using default settings. Error: {e}")
            return AuthConfig(
                debug_mode=DebugMode.PROD,
                permissions={},
                groups={}
            )

    #   Production mode is default for security reasons
    debug_mode_str = data.get('debug_mode', DebugMode.PROD).upper()
    try:
        debug_mode = DebugMode(debug_mode_str)
    except ValueError:
        if settings.ENVIRONMENT == DebugMode.PROD:
            raise ValueError(f"Invalid debug mode: {debug_mode_str}")
        else:
            print(f"WARNING: Invalid debug mode '{debug_mode_str}', using {DebugMode.PROD}")
            debug_mode = DebugMode.PROD

    #   Forbid setting any other mode in prod. Container won't start.
    if settings.ENVIRONMENT == DebugMode.PROD and debug_mode != DebugMode.PROD:
        raise ValueError(f"WARNING: access mode {debug_mode} is denied in {settings.ENVIRONMENT} environment")

    #   Warning that authentication system is off in production
    if settings.ENVIRONMENT == DebugMode.PROD and not settings.AUTH_ENABLED:
        print("WARNING: Auth system disabled!")

    permissions = {}
    permissions_data = data.get('permissions') or {}

    #   Put together permissions config from config file
    for method_code, access_level_str in permissions_data.items():
        method_code = method_code.lower()
        access_level_str = access_level_str.upper()

        try:
            access_level = AccessLevel(access_level_str)
        except ValueError:
            if settings.ENVIRONMENT == DebugMode.PROD:
                raise ValueError(f"Invalid access level '{access_level_str}' for method '{method_code}'")
            else:
                print(f"WARNING: Invalid access level '{access_level_str}' for method '{method_code}', skipping")
                continue

        permissions[method_code] = access_level

    groups = {}
    groups_data = data.get('groups') or {}

    for group_name, method_codes in groups_data.items():
        function_names = set()
        for method_code in method_codes:
            method_code = method_code.lower()
            if method_code in permissions:
                function_names.add(method_code)
            else:
                print(f"WARNING: Unknown method code '{method_code}' in group '{group_name}'")
        groups[group_name] = function_names

    return AuthConfig(
        debug_mode=debug_mode,
        permissions=permissions,
        groups=groups
    )


#   Permissions config validation at start-up
def validate_auth_config_on_startup(auth_config: AuthConfig):
    if auth_config.debug_mode == DebugMode.PROD:
        configured_methods_count = len(auth_config.permissions)

        if configured_methods_count == 0:
            print(f"WARNING: No methods configured in {DebugMode.PROD} mode! All methods will be blocked.")
        else:
            print(f"✅ Auth configuration loaded: {configured_methods_count} methods configured")
    else:
        print(f"🔧 DEV mode: {len(auth_config.permissions)} methods configured")


#   App authentication initialization
def _init_auth(app: FastAPI):
    try:
        auth_config = parse_auth()
        validate_auth_config_on_startup(auth_config)
        app.state.auth_config = auth_config
        print("✅ Authentication system initialized successfully")
    except Exception as e:
        if settings.ENVIRONMENT == DebugMode.PROD:
            print(f"CRITICAL: Failed to initialize auth system: {e}")
            raise
        else:
            print(f"❌ Auth system init failed, using safe defaults: {e}")
            app.state.auth_config = AuthConfig(
                debug_mode=DebugMode.PROD,
                permissions={},
                groups={}
            )
