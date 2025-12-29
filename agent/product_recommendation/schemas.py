"""Agent state and DTO schemas for product recommendation agent.

This module will contain:
- AgentState: LangGraph workflow state (TypedDict)
- DTOs: Database response objects (Pydantic models)
- Message DTOs: Node input/output schemas
"""

from typing import TypedDict, Literal
from pydantic import BaseModel


# Placeholder - will be implemented in later commits
class AgentState(TypedDict):
    """LangGraph state schema.
    
    To be implemented in Commit 5.
    """
    pass


class ProductDTO(BaseModel):
    """Placeholder DTO.
    
    To be implemented in Commit 5.
    """
    pass

