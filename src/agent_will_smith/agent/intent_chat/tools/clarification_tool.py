"""Clarification tool for intent chat agent.

Provides clarifying questions and options to gather user intent signals.
Returns structured data for UI rendering.
"""

from typing import Optional

import structlog
from langchain_core.tools import tool
from pydantic import BaseModel, Field


logger = structlog.get_logger(__name__)


class ClarificationToolInput(BaseModel):
    """Input schema for clarification tool."""

    question: str = Field(
        ...,
        description="The clarifying question to ask the user",
        min_length=1,
        max_length=500,
    )
    options: list[str] = Field(
        ...,
        description="List of options for the user to choose from",
        min_length=1,
    )
    category: Optional[str] = Field(
        default=None,
        description="Category of the clarification (e.g., 'risk_preference', 'life_stage')",
        max_length=50,
    )


def get_clarification(
    question: str,
    options: list[str],
    category: Optional[str] = None,
) -> dict:
    """Generate a clarification response with question and options.

    Args:
        question: The clarifying question to ask
        options: List of options for the user to choose from
        category: Optional category for the clarification

    Returns:
        Dict with question, options, category, and type

    Raises:
        ValueError: If question is empty or options list is empty
    """
    if not question or not question.strip():
        raise ValueError("question cannot be empty")

    if not options:
        raise ValueError("options must contain at least one option")

    logger.info(
        "clarification tool invoked",
        question_length=len(question),
        num_options=len(options),
        category=category,
    )

    return {
        "type": "clarification",
        "question": question,
        "options": options,
        "category": category,
    }


@tool("clarification", args_schema=ClarificationToolInput)
def clarification_tool(
    question: str,
    options: list[str],
    category: Optional[str] = None,
) -> dict:
    """Ask a clarifying question to better understand user intent.

    Use this tool when you need more information from the user to provide
    accurate recommendations. Present clear options that help identify
    the user's preferences, life stage, or risk tolerance.

    Args:
        question: The clarifying question to ask
        options: 2-5 clear options for the user to choose from
        category: Category for tracking (risk_preference, life_stage, product_interest)

    Returns:
        Structured clarification for UI rendering
    """
    return get_clarification(
        question=question,
        options=options,
        category=category,
    )
