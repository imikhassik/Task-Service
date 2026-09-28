"""
Stub for authentication off mode
"""
from enum import StrEnum
from typing import Dict, Set, Optional, Any
from pydantic import BaseModel
from fastapi import FastAPI

from .schema import AuthConfig, DebugMode, UserAuthInfo


#   Empty decorater - lets all requests through
def validate_permissions(permission_code: str = None):
    def decorator(func):
        return func
    return decorator


#   Configuration parser stub
def parse_auth() -> AuthConfig:
    return AuthConfig(debug_mode=DebugMode.DEV)


#   Config validation stub
def validate_auth_config_on_startup(auth_config: AuthConfig):
    print("🔓 Authentication disabled - all access granted")


#   Authentication disabled information
def get_lib_info(auth_config: AuthConfig) -> dict:
    return {
        "auth_enabled": False,
        "message": "Authentication system is disabled"
    }


#   Function access level in off mode
def get_function_access_level(auth_config: AuthConfig, function_name: str) -> str:
    return "OPEN (auth disabled)"


#   Initialization stub
def init_auth(app: FastAPI):
    app.state.auth_config = AuthConfig()
    print("🔓 Authentication system disabled - all access granted")
