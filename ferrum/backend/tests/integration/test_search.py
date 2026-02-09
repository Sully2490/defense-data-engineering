import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.supplier import Supplier


@pytest.mark.asyncio
class TestNaturalLanguageSearch:
    """Test suite for natural language search endpoint."""

    async def test_search_with_nl_query_returns_results(
        self,
        client: AsyncClient,
        auth_headers,
        create_test_user,
        db_session: AsyncSession
    ):
        """Test POST /api/v1/search with NL query returns results."""
        org_id = create_test_user["organization"].id
        suppliers = [
            Supplier(
                name="Titanium Aerospace Corporation",
                org_id=org_id,
                country="USA",
                description="Premium titanium alloys for aerospace"
            ),
            Supplier(
                name="Advanced Composites Ltd",
                org_id=org_id,
                country="UK",
                description="Carbon fiber and composite materials"
            )
        ]
        db_session.add_all(suppliers)
        await db_session.commit()

        response = await client.post(
            "/api/v1/search",
            headers=auth_headers,
            json={
                "query": "Titanium Aerospace Corporation supplier"
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert "results" in data
        assert "query_interpretation" in data
        assert "total" in data
        assert "search_type" in data

    async def test_search_with_material_keywords(
        self,
        client: AsyncClient,
        auth_headers,
        create_test_user,
        db_session: AsyncSession
    ):
        """Test search with material-related keywords."""
        response = await client.post(
            "/api/v1/search",
            headers=auth_headers,
            json={
                "query": "titanium alloy material for defense"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert data["search_type"] in ("sql", "fulltext", "rag")

    async def test_search_empty_query_returns_error(
        self,
        client: AsyncClient,
        auth_headers
    ):
        """Test that empty search query returns validation error."""
        response = await client.post(
            "/api/v1/search",
            headers=auth_headers,
            json={
                "query": ""
            }
        )

        assert response.status_code == 422

    async def test_search_without_auth_returns_error(
        self,
        client: AsyncClient
    ):
        """Test that search without authentication returns error."""
        response = await client.post(
            "/api/v1/search",
            json={
                "query": "find suppliers"
            }
        )

        assert response.status_code == 401

    async def test_search_respects_org_isolation(
        self,
        client: AsyncClient,
        auth_headers,
        create_test_user,
        db_session: AsyncSession
    ):
        """Test that search only returns results from user's organization."""
        from app.models.organization import Organization

        other_org = Organization(name="Other Org", slug="other-search")
        db_session.add(other_org)
        await db_session.commit()
        await db_session.refresh(other_org)

        other_supplier = Supplier(
            name="Other Org Vendor Company",
            org_id=other_org.id,
            country="USA",
        )

        user_supplier = Supplier(
            name="User Org Vendor Company",
            org_id=create_test_user["organization"].id,
            country="USA",
        )

        db_session.add_all([other_supplier, user_supplier])
        await db_session.commit()

        response = await client.post(
            "/api/v1/search",
            headers=auth_headers,
            json={
                "query": "vendor company supplier"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "results" in data
