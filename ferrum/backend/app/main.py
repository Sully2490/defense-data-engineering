"""FastAPI application factory for Ferrum."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.v1 import api_router
from .config import get_settings
from .middleware import AuditMiddleware, TenantMiddleware

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan events.

    Handles startup and shutdown events for the FastAPI application.
    """
    # Startup
    settings = get_settings()
    logger.info(f"Starting Ferrum API in {settings.ENV} environment")
    logger.info(f"Database: {settings.DATABASE_URL.split('@')[-1]}")  # Log without credentials
    logger.info(f"Neo4j: {settings.NEO4J_URI}")
    logger.info(f"CORS Origins: {settings.cors_origins_list}")

    # Auto-create tables for SQLite (dev mode)
    if "sqlite" in settings.DATABASE_URL:
        from .dependencies import async_engine
        from .models import Base
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("SQLite tables created")

    yield

    # Shutdown
    logger.info("Shutting down Ferrum API")


def create_app() -> FastAPI:
    """
    Application factory for creating FastAPI instance.

    Returns:
        FastAPI: Configured FastAPI application
    """
    settings = get_settings()

    app = FastAPI(
        title="Ferrum API",
        version="0.1.0",
        description="Defense supply chain intelligence and risk management platform. "
                    "Provides advanced analytics, compliance tracking, and semantic search "
                    "for defense contractors and materials sourcing.",
        lifespan=lifespan,
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add custom middleware
    app.add_middleware(TenantMiddleware)
    app.add_middleware(AuditMiddleware)

    # Include API v1 router
    app.include_router(api_router, prefix="/api/v1")

    # Health check endpoint
    @app.get("/health", tags=["health"])
    async def health_check():
        """
        Health check endpoint.

        Returns:
            dict: Health status
        """
        return {"status": "healthy"}

    return app


# Create application instance
app = create_app()
