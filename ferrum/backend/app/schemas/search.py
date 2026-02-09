"""Search schemas."""

from typing import Any, Optional

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    """AI-powered search request schema."""

    query: str = Field(..., min_length=1, description="Natural language search query")
    filters: Optional[dict[str, Any]] = Field(
        None, description="Additional structured filters"
    )


class SearchResponse(BaseModel):
    """Unified search response schema."""

    results: list[dict[str, Any]] = Field(..., description="Search results")
    query_interpretation: str = Field(
        ..., description="How the AI interpreted the query"
    )
    total: int = Field(..., description="Total number of results")
    facets: Optional[dict[str, Any]] = Field(
        None, description="Search facets for refinement"
    )
    search_type: str = Field(
        ..., description="Type of search performed (sql, rag, fulltext)"
    )
