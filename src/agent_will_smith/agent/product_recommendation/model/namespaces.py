"""Node namespace models for LangGraph state."""

from typing import Literal
from pydantic import BaseModel, Field
from agent_will_smith.agent.product_recommendation.model.types import VERTICALS
from agent_will_smith.agent.product_recommendation.model.product import ProductResult


class IntentNodeNamespace(BaseModel):
    """State namespace for intent analysis node."""
    intent: str = Field(..., min_length=10, max_length=1000)


class SearchNodeNamespace(BaseModel):
    """State namespace for parallel search node."""
    results: dict[VERTICALS, list[ProductResult]] = Field(default_factory=dict)
    status: Literal["complete", "partial"] = "complete"
    errors: dict[str, str] = Field(default_factory=dict)
