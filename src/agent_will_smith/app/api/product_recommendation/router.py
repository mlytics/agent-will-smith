"""API routes for product recommendation endpoints.

Follows guideline: "1 HTTP URL ↔ 1 agent"
Each endpoint maps to a single agent.
"""

from fastapi import APIRouter, Depends, Request
import structlog

from agent_will_smith.app.api.product_recommendation.dto import (
    RecommendProductsRequest,
    RecommendProductsResponse,
    ProductRecommendation,
    VerticalResults,
)
from dependency_injector.wiring import inject, Provide
from agent_will_smith.agent.product_recommendation.container import Container
from agent_will_smith.agent.product_recommendation.agent import Agent
from agent_will_smith.agent.product_recommendation.state import AgentInput
from agent_will_smith.core.exceptions import AgentStateError

router = APIRouter()


@router.post(
    "/recommend-products",
    response_model=RecommendProductsResponse,
    summary="Recommend products based on article and question",
    description="""
    Analyzes an article and question to recommend relevant products (activities and books).
    
    Implementation:
    - Uses Databricks vector search for semantic product retrieval
    - LangGraph workflow with injected dependencies
    - LLM reasoning for selection and ranking
    
    **Architecture:** DI Container pattern following joke_agent architecture.
    **Authentication:** Requires Bearer token in Authorization header.
    """,
    tags=["Recommendations"],
)
@inject
async def recommend_products_endpoint(
    request: Request,
    body: RecommendProductsRequest,
    agent: Agent = Depends(Provide[Container.agent]),
) -> RecommendProductsResponse:
    """Recommend products endpoint - maps 1:1 to Agent.

    Args:
        request: FastAPI request (for trace_id)
        body: Request payload with article, question, and k
        agent: Injected Agent from DI container

    Returns:
        List of recommended products with reasoning

    Raises:
        HTTPException: On agent failures or invalid inputs
    """
    logger = structlog.get_logger(__name__)
    trace_id = getattr(request.state, "trace_id", "unknown")

    logger.info(
        "recommend products request",
        trace_id=trace_id,
        article_length=len(body.article),
        question_length=len(body.question),
        k=body.k,
        product_types=body.product_types,
        customer_uuid=body.customer_uuid,
    )

    # Create AgentInput DTO from request body
    input_dto = AgentInput(
        article=body.article,
        question=body.question,
        k=body.k,
        verticals=body.product_types or ["activities", "books", "articles"],
        customer_uuid=body.customer_uuid,
    )

    # Invoke agent with DTO - returns AgentOutput DTO
    # Any exceptions will bubble to the global exception handler in main.py
    agent_output = await agent.invoke(input_dto)

    # Transform grouped results to API response format
    verticals_searched = body.product_types or ["activities", "books", "articles"]

    results_by_vertical = []
    for vertical in verticals_searched:
        vertical_products = agent_output.grouped_results.get(vertical, [])
        error = agent_output.errors.get(vertical)

        # Convert each product dict to ProductRecommendation with defensive checks
        try:
            products = [
                ProductRecommendation(
                    product_id=p["product_id"],
                    product_type=p["product_type"],
                    title=p["title"],
                    description=p.get("description"),
                    relevance_score=p["relevance_score"],
                    metadata=p.get("metadata", {}),
                )
                for p in vertical_products
            ]
        except (KeyError, TypeError) as e:
            # Internal state corruption - should never happen
            logger.error(
                "malformed agent output",
                vertical=vertical,
                error=str(e),
                raw_products=vertical_products,
            )
            raise AgentStateError(
                "Agent returned malformed product data",
                details={
                    "vertical": vertical,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "raw_products": vertical_products,
                },
                conflict=False,  # Programming error
            ) from e

        results_by_vertical.append(
            VerticalResults(
                vertical=vertical,
                products=products,
                count=len(products),
                error=error,
            )
        )

    logger.info(
        "recommend products success",
        trace_id=trace_id,
        total_products=agent_output.total_products,
        status=agent_output.status,
        verticals_searched=verticals_searched,
    )

    return RecommendProductsResponse(
        results_by_vertical=results_by_vertical,
        total_products=agent_output.total_products,
        reasoning=agent_output.intent,
        status=agent_output.status,
        verticals_searched=verticals_searched,
    )
