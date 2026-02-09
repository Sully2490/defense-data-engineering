"""Authentication service."""

import re
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models import Organization, User
from app.schemas.auth import TokenResponse


def _slugify(name: str) -> str:
    """Convert a name to a URL-safe slug."""
    slug = name.lower().strip()
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[\s_]+', '-', slug)
    return slug


async def create_user(
    session: AsyncSession,
    email: str,
    password: str,
    name: str,
    org_name: str,
    role: str = "org_admin",
) -> User:
    """Create a new user and organization.

    Args:
        session: Database session
        email: User email
        password: User password (will be hashed)
        name: User full name
        org_name: Organization name
        role: User role (defaults to org_admin for new orgs)

    Returns:
        Created user object

    Raises:
        HTTPException: If email already exists
    """
    # Check if user already exists
    result = await session.execute(select(User).where(User.email == email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create organization
    org = Organization(name=org_name, slug=_slugify(org_name))
    session.add(org)
    await session.flush()

    # Create user
    hashed_pw = hash_password(password)
    user = User(
        email=email,
        password_hash=hashed_pw,
        name=name,
        role=role,
        org_id=org.id,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)

    return user


async def authenticate_user(
    session: AsyncSession, email: str, password: str
) -> Optional[User]:
    """Authenticate a user by email and password.

    Args:
        session: Database session
        email: User email
        password: User password

    Returns:
        User object if authenticated, None otherwise
    """
    result = await session.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        return None

    if not verify_password(password, user.password_hash):
        return None

    return user


def create_tokens(user: User) -> TokenResponse:
    """Create access and refresh tokens for a user.

    Args:
        user: User object

    Returns:
        TokenResponse with access and refresh tokens
    """
    token_data = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role.value if hasattr(user.role, 'value') else str(user.role),
        "org_id": str(user.org_id),
    }

    access_token = create_access_token(token_data)
    refresh_token_str = create_refresh_token({"sub": str(user.id)})

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token_str,
        token_type="bearer",
    )


async def refresh_token(session: AsyncSession, refresh_token_str: str) -> TokenResponse:
    """Refresh an access token using a refresh token.

    Args:
        session: Database session
        refresh_token_str: Refresh token string

    Returns:
        New TokenResponse with fresh tokens

    Raises:
        HTTPException: If refresh token is invalid
    """
    try:
        payload = decode_token(refresh_token_str)
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )

        user_id = UUID(payload.get("sub"))
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )

        return create_tokens(user)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )
