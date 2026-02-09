"""SQL query generation for structured search."""

import json
import logging
from dataclasses import dataclass
from typing import Any

from anthropic import AsyncAnthropic

from .intent_classifier import IntentResult
from .prompts.sql_prompt import SQL_SYSTEM_PROMPT, SQL_USER_TEMPLATE

logger = logging.getLogger(__name__)


@dataclass
class GeneratedSQL:
    """Result of SQL generation."""

    sql: str
    params: dict[str, Any]
    explanation: str
    raw_response: dict[str, Any] | None = None


class SQLGenerator:
    """Generates SQL queries from natural language using Claude Sonnet."""

    def __init__(self, api_key: str):
        """Initialize the SQL generator.

        Args:
            api_key: Anthropic API key
        """
        self.client = AsyncAnthropic(api_key=api_key)
        self.model = "claude-sonnet-4-20250514"

    async def generate(
        self, query: str, intent: IntentResult, org_id: str
    ) -> GeneratedSQL:
        """Generate SQL query from natural language.

        Args:
            query: Natural language search query
            intent: Classified intent with extracted entities
            org_id: Organization ID for multi-tenant filtering

        Returns:
            GeneratedSQL with SQL query, parameters, and explanation

        Raises:
            Exception: If API call fails or response parsing fails
        """
        try:
            logger.info(f"Generating SQL for query: {query[:100]}...")

            # Format entities for the prompt
            entities_str = json.dumps(intent.entities, indent=2)

            user_prompt = SQL_USER_TEMPLATE.format(
                query=query,
                entities=entities_str,
            )

            response = await self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                temperature=0,
                system=SQL_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_prompt}],
            )

            # Extract text content from response
            content = response.content[0].text if response.content else ""

            # Parse JSON response
            result_data = json.loads(content)

            # Ensure org_id is always in params
            params = result_data.get("params", {})
            params["org_id"] = org_id

            generated_sql = GeneratedSQL(
                sql=result_data.get("sql", ""),
                params=params,
                explanation=result_data.get("explanation", ""),
                raw_response=result_data,
            )

            logger.info(f"Generated SQL: {generated_sql.explanation}")
            logger.debug(f"SQL query: {generated_sql.sql}")

            return generated_sql

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse SQL generation JSON: {e}")
            raise ValueError(f"Invalid SQL generation response: {e}")

        except Exception as e:
            logger.error(f"SQL generation failed: {e}")
            raise
