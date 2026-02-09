"""Permission and role-based access control."""

from enum import IntEnum

from fastapi import Depends, HTTPException, status

from app.models import RoleEnum


class RoleLevel(IntEnum):
    """Role hierarchy mapping roles to integer levels."""

    VIEWER = 0
    ANALYST = 1
    ADMIN = 2
    ORG_ADMIN = 3


ROLE_MAPPING = {
    RoleEnum.viewer: RoleLevel.VIEWER,
    RoleEnum.analyst: RoleLevel.ANALYST,
    RoleEnum.admin: RoleLevel.ADMIN,
    RoleEnum.org_admin: RoleLevel.ORG_ADMIN,
    "viewer": RoleLevel.VIEWER,
    "analyst": RoleLevel.ANALYST,
    "admin": RoleLevel.ADMIN,
    "org_admin": RoleLevel.ORG_ADMIN,
}


def check_permission(user_role, required_role) -> bool:
    """Check if a user role has sufficient permissions."""
    user_level = ROLE_MAPPING.get(user_role, RoleLevel.VIEWER)
    required_level = ROLE_MAPPING.get(required_role, RoleLevel.ORG_ADMIN)
    return user_level >= required_level
