"""Intent classification for search queries."""

import json
import logging
from dataclasses import dataclass
from typing import Any

from anthropic import AsyncAnthropic

from .prompts.intent_prompt import INTENT_SYSTEM_PROMPT, INTENT_USER_TEMPLATE

logger = logging.getLogger(__name__)


@dataclass
class IntentResult:
    """Result of intent classification."""

    intent: str  # structured_query | unstructured_query | hybrid | clarification_needed
    entities: dict[str, list[str]]
    confidence: float
    raw_response: dict[str, Any] | None = None


class IntentClassifier:
    """Classifies search query intent using Claude Haiku."""

    def __init__(self, api_key: str):
        """Initialize the intent classifier.

        Args:
            api_key: Anthropic API key
        """
        self.client = AsyncAnthropic(api_key=api_key)
        self.model = "claude-haiku-4-20250514"

    async def classify(self, query: str) -> IntentResult:
        """Classify a search query and extract entities.

        Args:
            query: Natural language search query

        Returns:
            IntentResult with intent type, entities, and confidence score

        Raises:
            Exception: If API call fails or response parsing fails
        """
        try:
            logger.info(f"Classifying query intent: {query[:100]}...")

            user_prompt = INTENT_USER_TEMPLATE.format(query=query)

            response = await self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                temperature=0,
                system=INTENT_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_prompt}],
            )

            # Extract text content from response
            content = response.content[0].text if response.content else ""

            # Parse JSON response
            result_data = json.loads(content)

            intent_result = IntentResult(
                intent=result_data.get("intent", "clarification_needed"),
                entities=result_data.get("entities", {}),
                confidence=result_data.get("confidence", 0.0),
                raw_response=result_data,
            )

            logger.info(
                f"Intent classified: {intent_result.intent} "
                f"(confidence: {intent_result.confidence:.2f})"
            )

            return intent_result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse intent classification JSON: {e}")
            # Return fallback result
            return IntentResult(
                intent="clarification_needed",
                entities={},
                confidence=0.0,
            )

        except Exception as e:
            logger.error(f"Intent classification failed: {e}")
            # Return fallback result instead of raising
            return IntentResult(
                intent="clarification_needed",
                entities={},
                confidence=0.0,
            )
