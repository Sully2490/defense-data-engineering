"""Row-Level Security (RLS) utilities for multi-tenancy."""

from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def set_rls_context(session: AsyncSession, org_id: UUID) -> None:
    """Set the RLS context for the current database session.

    Sets a PostgreSQL session variable that RLS policies use to filter data.
    """
    await session.execute(
        text("SET LOCAL app.current_org_id = :org_id"),
        {"org_id": str(org_id)},
    )


async def clear_rls_context(session: AsyncSession) -> None:
    """Clear the RLS context for the current database session."""
    await session.execute(text("RESET app.current_org_id"))
