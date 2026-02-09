"""Admin endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, require_role
from app.models import AuditLog, Organization, User, RoleEnum
from app.schemas.common import PaginationParams

router = APIRouter(prefix="/admin", tags=["admin"])


class OrgUpdate(BaseModel):
    name: str | None = None


@router.get("/audit-logs")
async def get_audit_logs(
    pagination: PaginationParams = Depends(),
    action: str | None = Query(None, description="Filter by action"),
    resource: str | None = Query(None, description="Filter by resource"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(RoleEnum.admin)),
):
    """Get paginated audit logs. Requires admin role."""
    query = select(AuditLog)

    if action:
        query = query.where(AuditLog.action == action)
    if resource:
        query = query.where(AuditLog.resource_type.ilike(f"%{resource}%"))

    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query) or 0

    query = query.order_by(AuditLog.timestamp.desc())
    query = query.offset((pagination.page - 1) * pagination.size).limit(pagination.size)

    result = await db.execute(query)
    logs = result.scalars().all()

    return {
        "items": logs,
        "total": total,
        "page": pagination.page,
        "size": pagination.size,
        "pages": (total + pagination.size - 1) // pagination.size,
    }


@router.get("/org")
async def get_org(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(RoleEnum.org_admin)),
):
    """Get organization details. Requires org_admin role."""
    result = await db.execute(
        select(Organization).where(Organization.id == current_user.org_id)
    )
    return result.scalar_one_or_none()


@router.put("/org")
async def update_org(
    org_update: OrgUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(RoleEnum.org_admin)),
):
    """Update organization details. Requires org_admin role."""
    result = await db.execute(
        select(Organization).where(Organization.id == current_user.org_id)
    )
    org = result.scalar_one_or_none()

    if org_update.name is not None:
        org.name = org_update.name

    await db.commit()
    await db.refresh(org)
    return org
