"""Export service for CSV generation."""

import csv
from io import StringIO

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Material, Supplier, User


async def export_suppliers_csv(
    session: AsyncSession, current_user: User, include_cui: bool = False
) -> str:
    """Export suppliers to CSV with CUI gating."""
    if include_cui and not current_user.cui_clearance:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CUI clearance required to export CUI data",
        )

    result = await session.execute(select(Supplier))
    suppliers = result.scalars().all()

    output = StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=[
            "name", "cage_code", "sam_uei", "duns_number",
            "city", "state", "country", "naics_codes",
            "small_business", "woman_owned", "veteran_owned", "hub_zone",
            "risk_score", "website", "contact_email",
        ],
    )
    writer.writeheader()

    for s in suppliers:
        if not include_cui and s.contains_cui:
            continue
        writer.writerow({
            "name": s.name,
            "cage_code": s.cage_code,
            "sam_uei": s.sam_uei,
            "duns_number": s.duns_number,
            "city": s.city,
            "state": s.state,
            "country": s.country,
            "naics_codes": ",".join(s.naics_codes) if s.naics_codes else "",
            "small_business": s.small_business,
            "woman_owned": s.woman_owned,
            "veteran_owned": s.veteran_owned,
            "hub_zone": s.hub_zone,
            "risk_score": s.risk_score,
            "website": s.website,
            "contact_email": s.contact_email,
        })

    return output.getvalue()


async def export_materials_csv(
    session: AsyncSession, current_user: User, include_cui: bool = False
) -> str:
    """Export materials to CSV."""
    if include_cui and not current_user.cui_clearance:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CUI clearance required to export CUI data",
        )

    result = await session.execute(select(Material))
    materials = result.scalars().all()

    output = StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=[
            "name", "specification", "grade", "form", "material_type",
            "nsn", "specialty_metal", "domestic_required", "export_controlled",
        ],
    )
    writer.writeheader()

    for m in materials:
        writer.writerow({
            "name": m.name,
            "specification": m.specification,
            "grade": m.grade,
            "form": m.form,
            "material_type": m.material_type,
            "nsn": m.nsn,
            "specialty_metal": m.specialty_metal,
            "domestic_required": m.domestic_required,
            "export_controlled": m.export_controlled,
        })

    return output.getvalue()
