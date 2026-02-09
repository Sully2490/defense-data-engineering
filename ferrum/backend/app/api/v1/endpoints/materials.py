"""Material endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_current_user, require_role
from app.models import User, RoleEnum
from app.schemas.common import PaginationParams
from app.schemas.material import (
    MaterialCategoryResponse,
    MaterialCreate,
    MaterialListResponse,
    MaterialResponse,
    MaterialUpdate,
)
from app.services.material_service import (
    create_material,
    get_material,
    list_categories,
    list_materials,
    update_material,
)

router = APIRouter(prefix="/materials", tags=["materials"])


@router.get("/", response_model=MaterialListResponse)
async def list_materials_endpoint(
    pagination: PaginationParams = Depends(),
    category: str | None = Query(None, description="Filter by category"),
    search_query: str | None = Query(None, description="Full-text search query"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MaterialListResponse:
    """List materials with filtering and pagination."""
    return await list_materials(
        session=db,
        page=pagination.page,
        size=pagination.size,
        category=category,
        search_query=search_query,
    )


@router.get("/categories", response_model=list[MaterialCategoryResponse])
async def list_categories_endpoint(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[MaterialCategoryResponse]:
    """List material categories."""
    return await list_categories(session=db)


@router.get("/{material_id}", response_model=MaterialResponse)
async def get_material_endpoint(
    material_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MaterialResponse:
    """Get material detail by ID."""
    return await get_material(session=db, material_id=material_id)


@router.post("/", response_model=MaterialResponse, status_code=status.HTTP_201_CREATED)
async def create_material_endpoint(
    material: MaterialCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(RoleEnum.analyst)),
) -> MaterialResponse:
    """Create a new material. Requires analyst role or higher."""
    return await create_material(
        session=db,
        material_data=material,
        org_id=current_user.org_id,
    )


@router.put("/{material_id}", response_model=MaterialResponse)
async def update_material_endpoint(
    material_id: UUID,
    material: MaterialUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(RoleEnum.analyst)),
) -> MaterialResponse:
    """Update an existing material. Requires analyst role or higher."""
    return await update_material(
        session=db,
        material_id=material_id,
        material_data=material,
    )
