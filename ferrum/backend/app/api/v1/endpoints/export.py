"""Export endpoints."""

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_current_user
from app.models import User
from app.services.export_service import export_materials_csv, export_suppliers_csv

router = APIRouter(prefix="/export", tags=["export"])


@router.get("/suppliers/csv")
async def export_suppliers_endpoint(
    include_cui: bool = Query(False, description="Include CUI data (requires clearance)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    """Export suppliers to CSV. Checks CUI access permissions."""
    csv_content = await export_suppliers_csv(
        session=db,
        current_user=current_user,
        include_cui=include_cui,
    )
    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=suppliers.csv"},
    )


@router.get("/materials/csv")
async def export_materials_endpoint(
    include_cui: bool = Query(False, description="Include CUI data (requires clearance)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    """Export materials to CSV. Checks CUI access permissions."""
    csv_content = await export_materials_csv(
        session=db,
        current_user=current_user,
        include_cui=include_cui,
    )
    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=materials.csv"},
    )
