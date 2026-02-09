"""AI-powered search endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_current_user
from app.models import User
from app.schemas.search import SearchRequest, SearchResponse
from app.services.search_service import execute_search

router = APIRouter(prefix="/search", tags=["search"])


@router.post("/", response_model=SearchResponse)
async def search_endpoint(
    request: SearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SearchResponse:
    """AI-powered natural language search.

    Orchestrates the AI pipeline:
    1. Intent classification (determine if SQL or RAG)
    2. SQL generation OR RAG retrieval
    3. Falls back to full-text search on AI failure
    """
    return await execute_search(session=db, search_request=request)
