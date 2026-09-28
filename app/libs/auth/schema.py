"""
Authentication system classes and schemas
"""
from enum import StrEnum
from typing import Dict, Set, Optional
from pydantic import BaseModel


class DebugMode(StrEnum):
    PROD = "PROD"
    DEV = "DEV"


class AccessLevel(StrEnum):
    GRANTED = "GRANTED"
    OPEN = "OPEN"
    AUTHORIZED = "AUTHORIZED"
    BLOCKED = "BLOCKED"


class AuthConfig(BaseModel):
    debug_mode: DebugMode
    permissions: Dict[str, AccessLevel] = {}    # function_name -> AccessLevel
    groups: Dict[str, Set[str]] = {}            # group_name -> set of function_names


#   User permissions information
class UserAuthInfo(BaseModel):
    user_permissions: Set[str]  # Explicitely specified permissions (in token)
    groups: Set[str]            # User groups
    all_permissions: Set[str]   # All permissions (explicit + group) 
    project_id: str             # Project ID for which permissions have been issued
