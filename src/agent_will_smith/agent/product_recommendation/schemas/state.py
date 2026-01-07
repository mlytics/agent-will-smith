"""LangGraph state schema for product recommendation agent.

See schemas/messages.py for additional agent schemas.
"""

from typing import Literal
from pydantic import BaseModel, Field
from agent_will_smith.agent.product_recommendation.schemas.types import VERTICALS
class AgentState(BaseModel):
    """LangGraph workflow state with Pydantic validation.
    
    This state is passed between nodes in the LangGraph workflow.
    LangGraph 0.2.x supports Pydantic BaseModel for automatic validation.
    
    Flow:
        Input → Intent Analysis → Parallel Search → Compose Response
        
    Benefits of Pydantic state:
    - Runtime validation at every state update
    - Early error detection
    - Type safety throughout workflow
    """
    # Input (from API request) - Required
    article: str = Field(..., min_length=10)
    question: str = Field(..., min_length=5)
    k: int = Field(..., ge=1, le=10)
    verticals: list[VERTICALS]
    customer_uuid: str | None = None
    
    # Intent Analysis Output (from LLM) - Optional
    intent: str | None = None
    
    # Search Results (full objects, no hydration needed) - Optional
    activities: list[dict] = Field(default_factory=list)
    books: list[dict] = Field(default_factory=list)
    articles: list[dict] = Field(default_factory=list)
    
    # Status Tracking - Optional
    status: Literal["complete", "partial"] = "complete"
    errors: dict[str, str] = Field(default_factory=dict)
    
    # Final Output (from compose node) - Optional
    grouped_results: dict[str, list[dict]] = Field(default_factory=dict)
    total_products: int = 0
