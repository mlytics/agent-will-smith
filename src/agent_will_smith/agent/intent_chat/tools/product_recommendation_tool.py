"""Product recommendation tool for intent chat agent.

Wraps the existing product_recommendation agent as a LangChain tool
for use in the intent chat workflow.
"""

from typing import Optional

import structlog
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from agent_will_smith.agent.product_recommendation.model.types import Vertical
from agent_will_smith.core.exceptions import AgentException


logger = structlog.get_logger(__name__)


class ProductRecommendationToolInput(BaseModel):
    """Input schema for product recommendation tool."""

    question: str = Field(
        ...,
        description="User question guiding the recommendation intent",
        min_length=5,
        max_length=500,
    )
    article: Optional[str] = Field(
        default=None,
        description="Optional article text to analyze for product recommendations. If not provided, recommendations are based on the question only.",
        max_length=50000,
    )
    k: int = Field(
        default=5,
        description="Number of products to recommend per vertical",
        ge=1,
        le=10,
    )
    verticals: list[str] = Field(
        default_factory=lambda: ["activities", "books"],
        description="Product verticals to search (activities, books, articles)",
    )
    customer_uuid: Optional[str] = Field(
        default=None,
        description="Customer UUID for multi-tenant data isolation",
    )


def get_product_recommendation_agent():
    """Lazy import to avoid circular dependencies.

    Returns a configured product recommendation agent instance.
    """
    from agent_will_smith.agent.product_recommendation.container import Container
    from agent_will_smith.core.container import Container as CoreContainer
    from agent_will_smith.infra.container import Container as InfraContainer

    core_container = CoreContainer()
    infra_container = InfraContainer(core_container=core_container)
    container = Container(core_container=core_container, infra_container=infra_container)
    return container.agent()


async def get_product_recommendations(
    question: str,
    article: Optional[str] = None,
    k: int = 5,
    verticals: Optional[list[str]] = None,
    customer_uuid: Optional[str] = None,
) -> dict:
    """Get product recommendations by invoking the product_recommendation agent.

    Args:
        question: User question guiding the recommendation
        article: Optional article text to analyze (if not provided, uses question only)
        k: Number of products per vertical
        verticals: Product verticals to search
        customer_uuid: Optional customer UUID for multi-tenant isolation

    Returns:
        Dict with grouped_results, total_products, status, errors, intent
    """
    if verticals is None:
        verticals = ["activities", "books"]

    logger.info(
        "product recommendation tool invoked",
        article_length=len(article) if article else 0,
        question_length=len(question),
        k=k,
        verticals=verticals,
        has_article=bool(article),
    )

    try:
        agent = get_product_recommendation_agent()

        from agent_will_smith.agent.product_recommendation.state import AgentInput

        input_dto = AgentInput(
            article=article,
            question=question,
            k=k,
            verticals=[Vertical(v) for v in verticals],
            customer_uuid=customer_uuid,
        )

        output = await agent.invoke(input_dto)

        logger.info(
            "product recommendation tool completed",
            total_products=output.total_products,
            status=output.status,
        )

        return output.model_dump()

    except AgentException as e:
        logger.error(
            "product recommendation tool failed",
            error=str(e),
            error_type=type(e).__name__,
        )
        return {
            "error": str(e),
            "error_type": type(e).__name__,
            "grouped_results": {},
            "total_products": 0,
            "status": "failed",
        }

    except Exception as e:
        logger.error(
            "product recommendation tool unexpected error",
            error=str(e),
            error_type=type(e).__name__,
        )
        return {
            "error": f"Unexpected error: {str(e)}",
            "error_type": type(e).__name__,
            "grouped_results": {},
            "total_products": 0,
            "status": "failed",
        }


@tool("product_recommendation", args_schema=ProductRecommendationToolInput)
async def product_recommendation_tool(
    question: str,
    article: Optional[str] = None,
    k: int = 5,
    verticals: Optional[list[str]] = None,
    customer_uuid: Optional[str] = None,
) -> dict:
    """Get product recommendations based on user question and optional article content.

    Searches for relevant products (activities, books, articles) using semantic search
    and LLM reasoning. Use this tool when the user shows clear intent to explore or
    purchase products related to topics in the conversation.

    Can work in two modes:
    - With article: Analyzes article content + question for contextual recommendations
    - Without article: Uses just the question to find relevant products

    Args:
        question: User question guiding what products to recommend
        article: Optional article text for additional context
        k: Number of products per vertical (1-10)
        verticals: Product types to search (activities, books, articles)
        customer_uuid: Optional customer ID for personalization

    Returns:
        Dictionary with product recommendations grouped by vertical
    """
    return await get_product_recommendations(
        question=question,
        article=article,
        k=k,
        verticals=verticals,
        customer_uuid=customer_uuid,
    )
