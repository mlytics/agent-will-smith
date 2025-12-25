"""MLFlow evaluation scorers for product recommendations.

Follows guideline: "Trace tool latency/cost separately from model cost."
Scorers help evaluate agent quality for MLFlow evaluations.
"""

from mlflow.genai import scorer
from agent.schemas import AgentResponse


@scorer
def has_sufficient_products(outputs: AgentResponse) -> bool:
    """Evaluate if agent returned at least one product recommendation.

    Args:
        outputs: Agent response with product recommendations

    Returns:
        True if at least one product was recommended
    """
    return len(outputs.products) > 0


@scorer
def relevance_score_quality(outputs: AgentResponse) -> float:
    """Evaluate average relevance score quality.

    Args:
        outputs: Agent response with product recommendations

    Returns:
        Average relevance score (0.0-1.0), or 0.0 if no products
    """
    if not outputs.products:
        return 0.0

    total_score = sum(p.relevance_score for p in outputs.products)
    return total_score / len(outputs.products)


@scorer
def has_reasoning(outputs: AgentResponse) -> bool:
    """Evaluate if agent provided reasoning for recommendations.

    Args:
        outputs: Agent response with reasoning

    Returns:
        True if reasoning is non-empty
    """
    return bool(outputs.reasoning and len(outputs.reasoning.strip()) > 0)


@scorer
def reasoning_quality(outputs: AgentResponse) -> int:
    """Evaluate reasoning length as a proxy for quality.

    Args:
        outputs: Agent response with reasoning

    Returns:
        Character count of reasoning (higher = more detailed)
    """
    return len(outputs.reasoning) if outputs.reasoning else 0


@scorer
def product_diversity(outputs: AgentResponse) -> float:
    """Evaluate diversity of product types in recommendations.

    Args:
        outputs: Agent response with product recommendations

    Returns:
        Diversity score (0.0-1.0): 1.0 if both activities and books, else 0.5
    """
    if not outputs.products:
        return 0.0

    product_types = set(p.product_type for p in outputs.products)

    # Perfect diversity = both types present
    if len(product_types) == 2:
        return 1.0
    # Partial diversity = only one type
    elif len(product_types) == 1:
        return 0.5
    # No products
    return 0.0

