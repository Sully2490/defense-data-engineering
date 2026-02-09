"""Material service."""

from math import ceil
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Material, MaterialCategory
from app.schemas.material import (
    MaterialCategoryResponse,
    MaterialCreate,
    MaterialListResponse,
    MaterialResponse,
    MaterialUpdate,
)


async def list_materials(
    session: AsyncSession,
    page: int = 1,
    size: int = 20,
    category: Optional[str] = None,
    search_query: Optional[str] = None,
) -> MaterialListResponse:
    """List materials with filtering and pagination."""
    query = select(Material)

    if category:
        query = query.join(MaterialCategory).where(
            MaterialCategory.name.ilike(f"%{category}%")
        )
    if search_query:
        search = f"%{search_query}%"
        query = query.where(
            or_(
                Material.name.ilike(search),
                Material.description.ilike(search),
                Material.specification.ilike(search),
            )
        )

    count_query = select(func.count()).select_from(query.subquery())
    total = await session.scalar(count_query) or 0

    query = query.offset((page - 1) * size).limit(size)

    result = await session.execute(query)
    materials = result.scalars().all()

    return MaterialListResponse(
        items=[MaterialResponse.model_validate(m) for m in materials],
        total=total,
        page=page,
        size=size,
        pages=ceil(total / size) if total > 0 else 0,
    )


async def get_material(session: AsyncSession, material_id: UUID) -> MaterialResponse:
    """Get material detail by ID."""
    result = await session.execute(
        select(Material).where(Material.id == material_id)
    )
    material = result.scalar_one_or_none()

    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Material {material_id} not found",
        )

    return MaterialResponse.model_validate(material)


async def create_material(
    session: AsyncSession, material_data: MaterialCreate, org_id: UUID
) -> MaterialResponse:
    """Create a new material."""
    material = Material(**material_data.model_dump(), org_id=org_id)
    session.add(material)
    await session.commit()
    await session.refresh(material)
    return MaterialResponse.model_validate(material)


async def update_material(
    session: AsyncSession, material_id: UUID, material_data: MaterialUpdate
) -> MaterialResponse:
    """Update an existing material."""
    result = await session.execute(select(Material).where(Material.id == material_id))
    material = result.scalar_one_or_none()

    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Material {material_id} not found",
        )

    update_data = material_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(material, field, value)

    await session.commit()
    await session.refresh(material)
    return MaterialResponse.model_validate(material)


async def list_categories(session: AsyncSession) -> list[MaterialCategoryResponse]:
    """List all material categories."""
    result = await session.execute(select(MaterialCategory))
    categories = result.scalars().all()
    return [MaterialCategoryResponse.model_validate(c) for c in categories]
