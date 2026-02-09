import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, RoleEnum
from app.models.organization import Organization
from app.core.security import hash_password


@pytest.mark.asyncio
class TestAuthRegistration:
    """Test suite for user registration endpoints."""

    async def test_register_creates_user_and_returns_tokens(self, client: AsyncClient):
        """Test POST /api/v1/auth/register creates user and returns tokens."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "securepassword123",
                "name": "New User",
                "org_name": "New Organization"
            }
        )

        assert response.status_code == 201
        data = response.json()

        assert "access_token" in data
        assert "refresh_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"

    async def test_register_duplicate_email_returns_error(self, client: AsyncClient, create_test_user):
        """Test registering with existing email returns error."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",  # Already exists from fixture
                "password": "password123",
                "name": "Duplicate User",
                "org_name": "Another Org"
            }
        )

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    async def test_register_invalid_email_returns_error(self, client: AsyncClient):
        """Test registration with invalid email format."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "notanemail",
                "password": "password123",
                "name": "Test User",
                "org_name": "Test Org"
            }
        )

        assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
class TestAuthLogin:
    """Test suite for user login endpoints."""

    async def test_login_valid_credentials_returns_tokens(self, client: AsyncClient, create_test_user):
        """Test POST /api/v1/auth/login with valid credentials returns tokens."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "testpassword123"
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert "access_token" in data
        assert "refresh_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"

    async def test_login_invalid_password_returns_401(self, client: AsyncClient, create_test_user):
        """Test POST /api/v1/auth/login with invalid password returns 401."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "wrongpassword"
            }
        )

        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()

    async def test_login_nonexistent_user_returns_401(self, client: AsyncClient):
        """Test POST /api/v1/auth/login with non-existent email returns 401."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "password123"
            }
        )

        assert response.status_code == 401

    async def test_login_inactive_user_returns_error(self, client: AsyncClient, db_session: AsyncSession):
        """Test login with inactive user account returns error on protected route."""
        from app.core.security import create_access_token

        org = Organization(name="Test Org", slug="test-inactive")
        db_session.add(org)
        await db_session.commit()
        await db_session.refresh(org)

        user = User(
            email="inactive@example.com",
            password_hash=hash_password("password123"),
            name="Inactive User",
            org_id=org.id,
            role=RoleEnum.viewer,
            is_active=False,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Login itself will return tokens (authenticate_user doesn't check is_active)
        # But accessing a protected endpoint will fail
        token = create_access_token(data={
            "sub": str(user.id),
            "email": user.email,
            "org_id": str(org.id),
            "role": user.role.value,
        })

        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 403


@pytest.mark.asyncio
class TestAuthMe:
    """Test suite for current user endpoint."""

    async def test_me_with_valid_token_returns_user(self, client: AsyncClient, auth_headers, create_test_user):
        """Test GET /api/v1/auth/me with valid token returns user."""
        response = await client.get(
            "/api/v1/auth/me",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        assert data["email"] == "test@example.com"
        assert data["name"] == "Test User"
        assert data["role"] == "analyst"
        assert "id" in data
        assert "org_id" in data

    async def test_me_without_token_returns_401(self, client: AsyncClient):
        """Test GET /api/v1/auth/me without token returns 401."""
        response = await client.get("/api/v1/auth/me")

        assert response.status_code == 401

    async def test_me_with_invalid_token_returns_401(self, client: AsyncClient):
        """Test GET /api/v1/auth/me with invalid token returns 401."""
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid.token.here"}
        )

        assert response.status_code == 401

    async def test_me_with_malformed_header_returns_error(self, client: AsyncClient):
        """Test GET /api/v1/auth/me with malformed authorization header."""
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "InvalidFormat"}
        )

        assert response.status_code in (401, 403)
