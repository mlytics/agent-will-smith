"""Node namespace models for LangGraph state."""

from typing import Literal
from pydantic import BaseModel, Field
from agent_will_smith.agent.product_recommendation.model.types import Vertical
from agent_will_smith.agent.product_recommendation.model.product import ProductResult


class IntentNodeNamespace(BaseModel):
    """State namespace for intent analysis node."""
    intent: str = Field(
        ...,
        description="LLM-generated intent analysis describing user's goals and article themes",
        min_length=10,
        max_length=1000,
        examples=["The user is interested in sustainable living practices. The article focuses on eco-friendly products and lifestyle changes."],
    )


class SearchNodeNamespace(BaseModel):
    """State namespace for parallel search node."""
    results: dict[Vertical, list[ProductResult]] = Field(
        default_factory=dict,
        description="Search results grouped by vertical (activities, books, articles)",
    )
    status: Literal["complete", "partial"] = Field(
        default="complete",
        description="Search completion status: 'complete' if all verticals succeeded, 'partial' if some failed",
        examples=["complete"],
    )
    errors: dict[str, str] = Field(
        default_factory=dict,
        description="Error messages by vertical for failed searches",
        examples=[{"activities": "UpstreamTimeoutError: Vector search timed out after 5.0s"}],
    )
