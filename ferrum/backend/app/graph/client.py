"""Neo4j async client for graph database operations."""

import logging
from typing import Any, Optional

from neo4j import AsyncGraphDatabase, AsyncDriver
from neo4j.exceptions import ServiceUnavailable, AuthError

from app.config import get_settings

logger = logging.getLogger(__name__)


class Neo4jClient:
    """Async Neo4j client using neo4j Python driver."""

    def __init__(self, uri: str, user: str, password: str):
        """Initialize Neo4j client with connection parameters.

        Args:
            uri: Neo4j connection URI (e.g., bolt://localhost:7687)
            user: Database username
            password: Database password
        """
        self.uri = uri
        self.user = user
        self.password = password
        self._driver: Optional[AsyncDriver] = None

    async def connect(self) -> None:
        """Establish connection to Neo4j and verify connectivity.

        Raises:
            ServiceUnavailable: If unable to connect to Neo4j
            AuthError: If authentication fails
        """
        try:
            self._driver = AsyncGraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password)
            )
            # Verify connectivity
            await self._driver.verify_connectivity()
            logger.info(f"Successfully connected to Neo4j at {self.uri}")
        except ServiceUnavailable as e:
            logger.error(f"Failed to connect to Neo4j at {self.uri}: {e}")
            raise
        except AuthError as e:
            logger.error(f"Authentication failed for Neo4j: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error connecting to Neo4j: {e}")
            raise

    async def close(self) -> None:
        """Close the Neo4j driver connection."""
        if self._driver:
            await self._driver.close()
            logger.info("Neo4j connection closed")

    async def execute_read(
        self,
        query: str,
        params: Optional[dict[str, Any]] = None
    ) -> list[dict[str, Any]]:
        """Execute a read transaction and return results as list of dicts.

        Args:
            query: Cypher query string (parameterized)
            params: Query parameters dictionary

        Returns:
            List of records as dictionaries

        Raises:
            RuntimeError: If driver is not connected
        """
        if not self._driver:
            raise RuntimeError("Neo4j driver not connected. Call connect() first.")

        params = params or {}

        async with self._driver.session() as session:
            try:
                result = await session.execute_read(
                    lambda tx: tx.run(query, params)
                )
                records = await result.data()
                logger.debug(f"Read query returned {len(records)} records")
                return records
            except Exception as e:
                logger.error(f"Error executing read query: {e}")
                logger.error(f"Query: {query}")
                logger.error(f"Params: {params}")
                raise

    async def execute_write(
        self,
        query: str,
        params: Optional[dict[str, Any]] = None
    ) -> list[dict[str, Any]]:
        """Execute a write transaction.

        Args:
            query: Cypher query string (parameterized)
            params: Query parameters dictionary

        Returns:
            List of records as dictionaries (if query returns data)

        Raises:
            RuntimeError: If driver is not connected
        """
        if not self._driver:
            raise RuntimeError("Neo4j driver not connected. Call connect() first.")

        params = params or {}

        async with self._driver.session() as session:
            try:
                result = await session.execute_write(
                    lambda tx: tx.run(query, params)
                )
                records = await result.data()
                logger.debug(f"Write query affected {len(records)} records")
                return records
            except Exception as e:
                logger.error(f"Error executing write query: {e}")
                logger.error(f"Query: {query}")
                logger.error(f"Params: {params}")
                raise

    async def __aenter__(self):
        """Context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        await self.close()


def get_neo4j_client() -> Neo4jClient:
    """Factory function to create Neo4jClient from application settings.

    Returns:
        Configured Neo4jClient instance (not yet connected)
    """
    settings = get_settings()
    return Neo4jClient(
        uri=settings.NEO4J_URI,
        user=settings.NEO4J_USER,
        password=settings.NEO4J_PASSWORD
    )
