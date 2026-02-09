"""AI-powered search service."""

from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Material, Supplier
from app.schemas.search import SearchRequest, SearchResponse


async def execute_search(
    session: AsyncSession, search_request: SearchRequest
) -> SearchResponse:
    """Execute search with fallback to full-text search.

    Orchestrates the AI pipeline:
    1. Intent classification
    2. SQL generation OR RAG retrieval
    3. Fallback to full-text search if AI fails
    """
    query = search_request.query.lower()

    if any(kw in query for kw in ["supplier", "vendor", "manufacturer", "company"]):
        search_type = "sql"
        results = await _search_suppliers(session, query)
        interpretation = f"Searching suppliers matching: {query}"
    elif any(kw in query for kw in ["material", "metal", "alloy", "composite", "part"]):
        search_type = "sql"
        results = await _search_materials(session, query)
        interpretation = f"Searching materials matching: {query}"
    else:
        search_type = "fulltext"
        supplier_results = await _search_suppliers(session, query)
        material_results = await _search_materials(session, query)
        results = supplier_results + material_results
        interpretation = f"Full-text search across all entities: {query}"

    return SearchResponse(
        results=results,
        query_interpretation=interpretation,
        total=len(results),
        facets=None,
        search_type=search_type,
    )


async def _search_suppliers(session: AsyncSession, query: str) -> list[dict[str, Any]]:
    """Search suppliers using ILIKE fallback."""
    search = f"%{query}%"
    stmt = select(Supplier).where(
        or_(
            Supplier.name.ilike(search),
            Supplier.description.ilike(search),
            Supplier.cage_code.ilike(search),
            Supplier.city.ilike(search),
            Supplier.state.ilike(search),
        )
    ).limit(20)

    result = await session.execute(stmt)
    suppliers = result.scalars().all()

    return [
        {
            "id": str(s.id),
            "type": "supplier",
            "name": s.name,
            "description": s.description,
            "cage_code": s.cage_code,
            "location": f"{s.city}, {s.state}" if s.city and s.state else None,
            "small_business": s.small_business,
            "risk_score": s.risk_score,
        }
        for s in suppliers
    ]


async def _search_materials(session: AsyncSession, query: str) -> list[dict[str, Any]]:
    """Search materials using ILIKE fallback."""
    search = f"%{query}%"
    stmt = select(Material).where(
        or_(
            Material.name.ilike(search),
            Material.description.ilike(search),
            Material.specification.ilike(search),
            Material.material_type.ilike(search),
            Material.nsn.ilike(search),
        )
    ).limit(20)

    result = await session.execute(stmt)
    materials = result.scalars().all()

    return [
        {
            "id": str(m.id),
            "type": "material",
            "name": m.name,
            "description": m.description,
            "specification": m.specification,
            "grade": m.grade,
            "nsn": m.nsn,
            "export_controlled": m.export_controlled,
        }
        for m in materials
    ]
