"""RAG (Retrieval Augmented Generation) engine for semantic search."""

import logging
from dataclasses import dataclass

from anthropic import AsyncAnthropic
from openai import AsyncOpenAI
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.embedding import DocumentEmbedding
from .prompts.rag_prompt import RAG_SYSTEM_PROMPT, RAG_USER_TEMPLATE

logger = logging.getLogger(__name__)


@dataclass
class Citation:
    """Citation for a RAG result."""

    source_type: str
    source_id: str
    content_snippet: str


@dataclass
class RAGResult:
    """Result of RAG search."""

    answer: str
    citations: list[Citation]
    confidence: float


class RAGEngine:
    """RAG engine for semantic document search and answer generation."""

    def __init__(
        self,
        anthropic_api_key: str,
        openai_api_key: str,
        top_k: int = 5,
    ):
        """Initialize the RAG engine.

        Args:
            anthropic_api_key: Anthropic API key for answer generation
            openai_api_key: OpenAI API key for embeddings
            top_k: Number of similar documents to retrieve (default: 5)
        """
        self.anthropic_client = AsyncAnthropic(api_key=anthropic_api_key)
        self.openai_client = AsyncOpenAI(api_key=openai_api_key)
        self.embedding_model = "text-embedding-3-small"
        self.generation_model = "claude-sonnet-4-20250514"
        self.top_k = top_k

    async def search(
        self, query: str, org_id: str, db: AsyncSession
    ) -> RAGResult:
        """Perform RAG search: embed query, retrieve similar docs, generate answer.

        Args:
            query: Natural language search query
            org_id: Organization ID for multi-tenant filtering
            db: Database session

        Returns:
            RAGResult with answer, citations, and confidence score

        Raises:
            Exception: If embedding or generation fails
        """
        try:
            logger.info(f"Starting RAG search for query: {query[:100]}...")

            # Step 1: Generate embedding for the query
            query_embedding = await self._embed_query(query)

            # Step 2: Retrieve similar documents using vector search
            documents = await self._retrieve_similar_documents(
                query_embedding, org_id, db
            )

            # Handle case where no documents found
            if not documents:
                logger.warning("No relevant documents found for query")
                return RAGResult(
                    answer=(
                        "I couldn't find any relevant information in the available "
                        "documents to answer your question. Please try rephrasing "
                        "your query or ask about a different topic."
                    ),
                    citations=[],
                    confidence=0.1,
                )

            # Step 3: Build context from retrieved documents
            context = self._build_context(documents)

            # Step 4: Generate answer using Claude Sonnet
            answer = await self._generate_answer(query, context)

            # Step 5: Build citations
            citations = [
                Citation(
                    source_type=doc["source_type"],
                    source_id=str(doc["source_id"]),
                    content_snippet=doc["content"][:200] + "...",
                )
                for doc in documents
            ]

            # Calculate confidence based on number and quality of results
            confidence = min(0.9, 0.5 + (len(documents) * 0.1))

            logger.info(f"RAG search completed with {len(citations)} citations")

            return RAGResult(
                answer=answer,
                citations=citations,
                confidence=confidence,
            )

        except Exception as e:
            logger.error(f"RAG search failed: {e}")
            raise

    async def _embed_query(self, query: str) -> list[float]:
        """Generate embedding for query using OpenAI.

        Args:
            query: Query text to embed

        Returns:
            Embedding vector as list of floats
        """
        try:
            response = await self.openai_client.embeddings.create(
                model=self.embedding_model,
                input=query,
            )
            embedding = response.data[0].embedding
            logger.debug(f"Generated query embedding with {len(embedding)} dimensions")
            return embedding

        except Exception as e:
            logger.error(f"Failed to generate query embedding: {e}")
            raise

    async def _retrieve_similar_documents(
        self,
        query_embedding: list[float],
        org_id: str,
        db: AsyncSession,
    ) -> list[dict]:
        """Retrieve similar documents using pgvector cosine similarity.

        Args:
            query_embedding: Query embedding vector
            org_id: Organization ID for filtering
            db: Database session

        Returns:
            List of document dictionaries with source info and content
        """
        try:
            # Convert embedding to string for SQL
            embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"

            # Query using pgvector's <=> cosine distance operator
            # Lower distance = more similar
            query = text("""
                SELECT
                    id,
                    source_type,
                    source_id,
                    content,
                    embedding <=> :embedding::vector AS distance
                FROM document_embeddings
                WHERE org_id = :org_id
                  AND embedding IS NOT NULL
                ORDER BY embedding <=> :embedding::vector
                LIMIT :limit
            """)

            result = await db.execute(
                query,
                {
                    "embedding": embedding_str,
                    "org_id": org_id,
                    "limit": self.top_k,
                },
            )

            rows = result.fetchall()

            documents = [
                {
                    "id": row.id,
                    "source_type": row.source_type,
                    "source_id": row.source_id,
                    "content": row.content,
                    "distance": row.distance,
                }
                for row in rows
            ]

            logger.info(f"Retrieved {len(documents)} similar documents")
            return documents

        except Exception as e:
            logger.error(f"Failed to retrieve similar documents: {e}")
            # Return empty list instead of raising to allow graceful degradation
            return []

    def _build_context(self, documents: list[dict]) -> str:
        """Build context string from retrieved documents.

        Args:
            documents: List of document dictionaries

        Returns:
            Formatted context string
        """
        context_parts = []

        for i, doc in enumerate(documents, 1):
            context_parts.append(
                f"[Source {i}] ({doc['source_type']} - ID: {doc['source_id']})\n"
                f"{doc['content']}\n"
            )

        return "\n".join(context_parts)

    async def _generate_answer(self, query: str, context: str) -> str:
        """Generate answer using Claude Sonnet with retrieved context.

        Args:
            query: Original user query
            context: Retrieved document context

        Returns:
            Generated answer text
        """
        try:
            user_prompt = RAG_USER_TEMPLATE.format(
                context=context,
                query=query,
            )

            response = await self.anthropic_client.messages.create(
                model=self.generation_model,
                max_tokens=2048,
                temperature=0.3,
                system=RAG_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_prompt}],
            )

            answer = response.content[0].text if response.content else ""

            logger.debug(f"Generated answer: {answer[:100]}...")
            return answer

        except Exception as e:
            logger.error(f"Failed to generate answer: {e}")
            raise
