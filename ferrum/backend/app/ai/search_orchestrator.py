"""Search orchestrator for coordinating AI search pipeline."""

import asyncio
import logging
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..schemas.search import SearchResponse
from .intent_classifier import IntentClassifier, IntentResult
from .rag_engine import RAGEngine
from .sql_generator import SQLGenerator
from .validators.sql_validator import SQLValidator

logger = logging.getLogger(__name__)


class SearchOrchestrator:
    """Orchestrates the complete AI search pipeline."""

    def __init__(
        self,
        anthropic_api_key: str,
        openai_api_key: str,
    ):
        """Initialize the search orchestrator.

        Args:
            anthropic_api_key: Anthropic API key for Claude models
            openai_api_key: OpenAI API key for embeddings
        """
        self.intent_classifier = IntentClassifier(api_key=anthropic_api_key)
        self.sql_generator = SQLGenerator(api_key=anthropic_api_key)
        self.rag_engine = RAGEngine(
            anthropic_api_key=anthropic_api_key,
            openai_api_key=openai_api_key,
        )

    async def orchestrate(
        self,
        query: str,
        org_id: str,
        db: AsyncSession,
        cui_authorized: bool = False,
    ) -> SearchResponse:
        """Orchestrate the complete search pipeline.

        Args:
            query: Natural language search query
            org_id: Organization ID for multi-tenant filtering
            db: Database session
            cui_authorized: Whether user is authorized for CUI data access

        Returns:
            SearchResponse with results, interpretation, and metadata
        """
        try:
            logger.info(f"Starting search orchestration for query: {query[:100]}...")

            # Step 1: Classify intent
            intent = await self.intent_classifier.classify(query)

            logger.info(f"Intent classified as: {intent.intent}")

            # Step 2: Route based on intent
            if intent.intent == "clarification_needed":
                return await self._handle_clarification(query, intent)

            elif intent.intent == "structured_query":
                return await self._handle_structured_search(
                    query, intent, org_id, db, cui_authorized
                )

            elif intent.intent == "unstructured_query":
                return await self._handle_rag_search(query, org_id, db)

            elif intent.intent == "hybrid":
                return await self._handle_hybrid_search(
                    query, intent, org_id, db, cui_authorized
                )

            else:
                # Unknown intent, fall back to clarification
                return await self._handle_clarification(query, intent)

        except Exception as e:
            logger.error(f"Search orchestration failed: {e}")
            # Fall back to full-text search
            return await self._fallback_fulltext_search(query, org_id, db)

    async def _handle_clarification(
        self, query: str, intent: IntentResult
    ) -> SearchResponse:
        """Handle queries that need clarification.

        Args:
            query: Original query
            intent: Intent classification result

        Returns:
            SearchResponse with clarification message
        """
        clarification_message = (
            f"I need more information to answer your query: '{query}'. "
            "Could you please provide more details? For example:\n"
            "- Specific supplier names or material types\n"
            "- Location or certification requirements\n"
            "- Compliance or capability needs"
        )

        return SearchResponse(
            results=[],
            query_interpretation=clarification_message,
            total=0,
            facets={},
            search_type="clarification",
        )

    async def _handle_structured_search(
        self,
        query: str,
        intent: IntentResult,
        org_id: str,
        db: AsyncSession,
        cui_authorized: bool,
    ) -> SearchResponse:
        """Handle structured database queries.

        Args:
            query: Original query
            intent: Intent classification result
            org_id: Organization ID
            db: Database session
            cui_authorized: CUI authorization status

        Returns:
            SearchResponse with SQL query results
        """
        try:
            # Generate SQL
            generated_sql = await self.sql_generator.generate(query, intent, org_id)

            # Validate SQL
            validator = SQLValidator(cui_authorized=cui_authorized)
            validation = validator.validate(generated_sql.sql)

            if not validation.is_valid:
                logger.warning(
                    f"SQL validation failed: {', '.join(validation.errors)}"
                )
                # Fall back to full-text search
                return await self._fallback_fulltext_search(query, org_id, db)

            # Execute validated SQL
            results = await self._execute_sql(
                validation.sanitized_sql,
                generated_sql.params,
                db,
            )

            # Build facets from results
            facets = self._build_facets(results)

            return SearchResponse(
                results=results,
                query_interpretation=generated_sql.explanation,
                total=len(results),
                facets=facets,
                search_type="sql",
            )

        except Exception as e:
            logger.error(f"Structured search failed: {e}")
            return await self._fallback_fulltext_search(query, org_id, db)

    async def _handle_rag_search(
        self, query: str, org_id: str, db: AsyncSession
    ) -> SearchResponse:
        """Handle unstructured RAG searches.

        Args:
            query: Original query
            org_id: Organization ID
            db: Database session

        Returns:
            SearchResponse with RAG answer and citations
        """
        try:
            rag_result = await self.rag_engine.search(query, org_id, db)

            # Format RAG result as search response
            results = [
                {
                    "answer": rag_result.answer,
                    "citations": [
                        {
                            "source_type": citation.source_type,
                            "source_id": citation.source_id,
                            "snippet": citation.content_snippet,
                        }
                        for citation in rag_result.citations
                    ],
                }
            ]

            return SearchResponse(
                results=results,
                query_interpretation=f"Retrieved {len(rag_result.citations)} relevant sources",
                total=1,
                facets={"confidence": rag_result.confidence},
                search_type="rag",
            )

        except Exception as e:
            logger.error(f"RAG search failed: {e}")
            return await self._fallback_fulltext_search(query, org_id, db)

    async def _handle_hybrid_search(
        self,
        query: str,
        intent: IntentResult,
        org_id: str,
        db: AsyncSession,
        cui_authorized: bool,
    ) -> SearchResponse:
        """Handle hybrid searches (both SQL and RAG).

        Args:
            query: Original query
            intent: Intent classification result
            org_id: Organization ID
            db: Database session
            cui_authorized: CUI authorization status

        Returns:
            SearchResponse with merged SQL and RAG results
        """
        try:
            # Execute both searches in parallel
            structured_task = self._handle_structured_search(
                query, intent, org_id, db, cui_authorized
            )
            rag_task = self._handle_rag_search(query, org_id, db)

            structured_response, rag_response = await asyncio.gather(
                structured_task, rag_task, return_exceptions=True
            )

            # Handle exceptions
            if isinstance(structured_response, Exception):
                logger.error(f"Structured search failed in hybrid: {structured_response}")
                structured_response = None

            if isinstance(rag_response, Exception):
                logger.error(f"RAG search failed in hybrid: {rag_response}")
                rag_response = None

            # Merge results
            merged_results = []
            query_interpretation = "Hybrid search results: "

            if structured_response and structured_response.results:
                merged_results.extend(
                    [{"type": "structured", **r} for r in structured_response.results]
                )
                query_interpretation += f"{len(structured_response.results)} database results"

            if rag_response and rag_response.results:
                merged_results.extend(
                    [{"type": "rag", **r} for r in rag_response.results]
                )
                if structured_response and structured_response.results:
                    query_interpretation += " and "
                query_interpretation += "document-based answer"

            # If both failed, fall back
            if not merged_results:
                return await self._fallback_fulltext_search(query, org_id, db)

            return SearchResponse(
                results=merged_results,
                query_interpretation=query_interpretation,
                total=len(merged_results),
                facets={},
                search_type="hybrid",
            )

        except Exception as e:
            logger.error(f"Hybrid search failed: {e}")
            return await self._fallback_fulltext_search(query, org_id, db)

    async def _execute_sql(
        self, sql: str, params: dict[str, Any], db: AsyncSession
    ) -> list[dict[str, Any]]:
        """Execute validated SQL query.

        Args:
            sql: SQL query string
            params: Query parameters
            db: Database session

        Returns:
            List of result dictionaries
        """
        try:
            result = await db.execute(text(sql), params)
            rows = result.fetchall()

            # Convert rows to dictionaries
            results = []
            for row in rows:
                row_dict = dict(row._mapping)
                # Convert UUIDs to strings for JSON serialization
                for key, value in row_dict.items():
                    if hasattr(value, "hex"):  # UUID check
                        row_dict[key] = str(value)
                results.append(row_dict)

            logger.info(f"SQL query returned {len(results)} results")
            return results

        except Exception as e:
            logger.error(f"SQL execution failed: {e}")
            raise

    async def _fallback_fulltext_search(
        self, query: str, org_id: str, db: AsyncSession
    ) -> SearchResponse:
        """Fallback to PostgreSQL full-text search.

        Args:
            query: Search query
            org_id: Organization ID
            db: Database session

        Returns:
            SearchResponse with full-text search results
        """
        try:
            logger.info("Using fallback full-text search")

            # Search suppliers using tsvector
            suppliers_query = text("""
                SELECT
                    id,
                    name,
                    description,
                    city,
                    state,
                    'supplier' AS type,
                    ts_rank(search_vector, plainto_tsquery('english', :query)) AS rank
                FROM suppliers
                WHERE org_id = :org_id
                  AND search_vector @@ plainto_tsquery('english', :query)
                ORDER BY rank DESC
                LIMIT 50
            """)

            # Search materials using tsvector (assuming materials has search_vector)
            materials_query = text("""
                SELECT
                    id,
                    name,
                    description,
                    category,
                    'material' AS type,
                    ts_rank(search_vector, plainto_tsquery('english', :query)) AS rank
                FROM materials
                WHERE org_id = :org_id
                  AND search_vector @@ plainto_tsquery('english', :query)
                ORDER BY rank DESC
                LIMIT 50
            """)

            # Execute both queries
            suppliers_result = await db.execute(
                suppliers_query, {"query": query, "org_id": org_id}
            )
            materials_result = await db.execute(
                materials_query, {"query": query, "org_id": org_id}
            )

            suppliers = [dict(row._mapping) for row in suppliers_result.fetchall()]
            materials = [dict(row._mapping) for row in materials_result.fetchall()]

            # Convert UUIDs to strings
            for item in suppliers + materials:
                for key, value in item.items():
                    if hasattr(value, "hex"):
                        item[key] = str(value)

            # Combine and sort by rank
            all_results = suppliers + materials
            all_results.sort(key=lambda x: x.get("rank", 0), reverse=True)

            return SearchResponse(
                results=all_results[:100],  # Limit to 100 total results
                query_interpretation="Full-text search results (AI search unavailable)",
                total=len(all_results[:100]),
                facets={},
                search_type="fulltext",
            )

        except Exception as e:
            logger.error(f"Fallback full-text search failed: {e}")
            # Return empty results rather than raising
            return SearchResponse(
                results=[],
                query_interpretation="Search failed. Please try a different query.",
                total=0,
                facets={},
                search_type="error",
            )

    def _build_facets(self, results: list[dict[str, Any]]) -> dict[str, Any]:
        """Build facets from search results for filtering.

        Args:
            results: Search results

        Returns:
            Dictionary of facets
        """
        facets: dict[str, Any] = {
            "states": {},
            "certifications": {},
            "business_types": {},
        }

        for result in results:
            # Count states
            if "state" in result and result["state"]:
                state = result["state"]
                facets["states"][state] = facets["states"].get(state, 0) + 1

            # Count business types
            if result.get("small_business"):
                facets["business_types"]["small_business"] = (
                    facets["business_types"].get("small_business", 0) + 1
                )
            if result.get("woman_owned"):
                facets["business_types"]["woman_owned"] = (
                    facets["business_types"].get("woman_owned", 0) + 1
                )
            if result.get("veteran_owned"):
                facets["business_types"]["veteran_owned"] = (
                    facets["business_types"].get("veteran_owned", 0) + 1
                )

        return facets
