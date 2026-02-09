"""API v1 router configuration."""

from fastapi import APIRouter

from .endpoints import admin, auth, export, materials, search, suppliers

# Create the main v1 router
api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(suppliers.router)
api_router.include_router(materials.router)
api_router.include_router(search.router)
api_router.include_router(admin.router)
api_router.include_router(export.router)
