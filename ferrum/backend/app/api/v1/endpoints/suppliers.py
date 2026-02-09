"""Supplier endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_current_user, require_role
from app.models import User, RoleEnum
from app.schemas.common import MessageResponse, PaginationParams
from app.schemas.supplier import (
    SupplierCreate,
    SupplierFilters,
    SupplierListResponse,
    SupplierResponse,
    SupplierUpdate,
)
from app.services.supplier_service import (
    create_supplier,
    delete_supplier,
    get_supplier,
    list_suppliers,
    update_supplier,
)

router = APIRouter(prefix="/suppliers", tags=["suppliers"])


@router.get("/", response_model=SupplierListResponse)
async def list_suppliers_endpoint(
    pagination: PaginationParams = Depends(),
    naics_code: str | None = Query(None, description="Filter by NAICS code"),
    state: str | None = Query(None, description="Filter by state"),
    country: str | None = Query(None, description="Filter by country"),
    small_business: bool | None = Query(None, description="Filter by small business status"),
    certification: str | None = Query(None, description="Filter by certification type"),
    capability: str | None = Query(None, description="Filter by capability type"),
    search_query: str | None = Query(None, description="Full-text search query"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SupplierListResponse:
    """List suppliers with filtering and pagination."""
    filters = SupplierFilters(
        naics_code=naics_code,
        state=state,
        country=country,
        small_business=small_business,
        certification=certification,
        capability=capability,
        search_query=search_query,
    )
    return await list_suppliers(
        session=db,
        page=pagination.page,
        size=pagination.size,
        filters=filters,
    )


@router.get("/{supplier_id}", response_model=SupplierResponse)
async def get_supplier_endpoint(
    supplier_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SupplierResponse:
    """Get supplier detail by ID."""
    return await get_supplier(session=db, supplier_id=supplier_id)


@router.post("/", response_model=SupplierResponse, status_code=status.HTTP_201_CREATED)
async def create_supplier_endpoint(
    supplier: SupplierCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(RoleEnum.analyst)),
) -> SupplierResponse:
    """Create a new supplier. Requires analyst role or higher."""
    return await create_supplier(
        session=db,
        supplier_data=supplier,
        org_id=current_user.org_id,
    )


@router.put("/{supplier_id}", response_model=SupplierResponse)
async def update_supplier_endpoint(
    supplier_id: UUID,
    supplier: SupplierUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(RoleEnum.analyst)),
) -> SupplierResponse:
    """Update an existing supplier. Requires analyst role or higher."""
    return await update_supplier(
        session=db,
        supplier_id=supplier_id,
        supplier_data=supplier,
    )


@router.delete("/{supplier_id}", response_model=MessageResponse)
async def delete_supplier_endpoint(
    supplier_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(RoleEnum.admin)),
) -> MessageResponse:
    """Soft delete a supplier. Requires admin role."""
    await delete_supplier(session=db, supplier_id=supplier_id)
    return MessageResponse(message=f"Supplier {supplier_id} deleted successfully")
