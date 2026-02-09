"""Supplier service."""

from math import ceil
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Supplier
from app.schemas.supplier import (
    SupplierCreate,
    SupplierFilters,
    SupplierListResponse,
    SupplierResponse,
    SupplierUpdate,
)


async def list_suppliers(
    session: AsyncSession,
    page: int = 1,
    size: int = 20,
    filters: Optional[SupplierFilters] = None,
) -> SupplierListResponse:
    """List suppliers with filtering and pagination."""
    query = select(Supplier)

    if filters:
        if filters.naics_code:
            query = query.where(Supplier.naics_codes.any(filters.naics_code))
        if filters.state:
            query = query.where(Supplier.state == filters.state)
        if filters.country:
            query = query.where(Supplier.country == filters.country)
        if filters.small_business is not None:
            query = query.where(Supplier.small_business == filters.small_business)
        if filters.search_query:
            search = f"%{filters.search_query}%"
            query = query.where(
                or_(
                    Supplier.name.ilike(search),
                    Supplier.description.ilike(search),
                    Supplier.cage_code.ilike(search),
                )
            )

    count_query = select(func.count()).select_from(query.subquery())
    total = await session.scalar(count_query) or 0

    query = query.offset((page - 1) * size).limit(size)

    result = await session.execute(query)
    suppliers = result.scalars().all()

    return SupplierListResponse(
        items=[SupplierResponse.model_validate(s) for s in suppliers],
        total=total,
        page=page,
        size=size,
        pages=ceil(total / size) if total > 0 else 0,
    )


async def get_supplier(session: AsyncSession, supplier_id: UUID) -> SupplierResponse:
    """Get supplier detail by ID."""
    result = await session.execute(
        select(Supplier).where(Supplier.id == supplier_id)
    )
    supplier = result.scalar_one_or_none()

    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Supplier {supplier_id} not found",
        )

    return SupplierResponse.model_validate(supplier)


async def create_supplier(
    session: AsyncSession, supplier_data: SupplierCreate, org_id: UUID
) -> SupplierResponse:
    """Create a new supplier."""
    supplier = Supplier(**supplier_data.model_dump(), org_id=org_id)
    session.add(supplier)
    await session.commit()
    await session.refresh(supplier)
    return SupplierResponse.model_validate(supplier)


async def update_supplier(
    session: AsyncSession, supplier_id: UUID, supplier_data: SupplierUpdate
) -> SupplierResponse:
    """Update an existing supplier."""
    result = await session.execute(select(Supplier).where(Supplier.id == supplier_id))
    supplier = result.scalar_one_or_none()

    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Supplier {supplier_id} not found",
        )

    update_data = supplier_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(supplier, field, value)

    await session.commit()
    await session.refresh(supplier)
    return SupplierResponse.model_validate(supplier)


async def delete_supplier(session: AsyncSession, supplier_id: UUID) -> None:
    """Delete a supplier."""
    result = await session.execute(select(Supplier).where(Supplier.id == supplier_id))
    supplier = result.scalar_one_or_none()

    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Supplier {supplier_id} not found",
        )

    await session.delete(supplier)
    await session.commit()
