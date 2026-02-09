import os
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from typing import AsyncGenerator, Dict

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test.db")
os.environ.setdefault("DATABASE_URL_SYNC", "sqlite:///./test.db")
os.environ.setdefault("NEO4J_URI", "bolt://localhost:7687")
os.environ.setdefault("NEO4J_USER", "neo4j")
os.environ.setdefault("NEO4J_PASSWORD", "test")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-testing")

from app.main import app
from app.models import Base, Organization, User, RoleEnum
from app.dependencies import get_db
from app.core.security import create_access_token, hash_password


TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "sqlite+aiosqlite:///./test.db")

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    poolclass=NullPool,
    echo=False,
)

TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh database session for each test."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create an async HTTP client with test database."""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test", follow_redirects=True) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def create_test_user(db_session: AsyncSession) -> Dict:
    """Create a test organization and user, return user data with token."""
    org = Organization(
        name="Test Organization",
        slug="test-org",
    )
    db_session.add(org)
    await db_session.commit()
    await db_session.refresh(org)

    user = User(
        email="test@example.com",
        password_hash=hash_password("testpassword123"),
        name="Test User",
        org_id=org.id,
        role=RoleEnum.analyst,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    token = create_access_token(
        data={
            "sub": str(user.id),
            "email": user.email,
            "org_id": str(org.id),
            "role": user.role.value,
        }
    )

    return {
        "user": user,
        "organization": org,
        "token": token,
        "password": "testpassword123",
    }


@pytest_asyncio.fixture
async def auth_headers(create_test_user: Dict) -> Dict[str, str]:
    """Return authorization headers with valid token."""
    return {"Authorization": f"Bearer {create_test_user['token']}"}
