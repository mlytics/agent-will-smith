"""API routes for product recommendation endpoints.

Follows guideline: "1 HTTP URL ↔ 1 agent"
Each endpoint maps to a single agent.
"""

import time
from fastapi import APIRouter, Depends, Request, HTTPException
import structlog

from src.core.exceptions import map_exception_to_http_status, AgentException
from src.app.api.product_recommendation.dto.schemas import (
    RecommendProductsRequest,
    RecommendProductsResponse,
    ProductRecommendation,
    VerticalResults,
)
from dependency_injector.wiring import inject, Provide
from src.agent.product_recommendation.container import Container
from src.agent.product_recommendation.product_recommendation_agent import ProductRecommendationAgent

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
    agent: ProductRecommendationAgent = Depends(Provide[Container.agent]),
    logger: structlog.BoundLogger = Depends(Provide[Container.logger]),
) -> RecommendProductsResponse:
    """Recommend products endpoint - maps 1:1 to ProductRecommendationAgent.

    Args:
        request: FastAPI request (for trace_id)
        body: Request payload with article, question, and k
        agent: Injected ProductRecommendationAgent from DI container
        logger: Injected logger from DI container

    Returns:
        List of recommended products with reasoning

    Raises:
        HTTPException: On agent failures or invalid inputs
    """
    trace_id = getattr(request.state, "trace_id", "unknown")

    logger.info(
        "recommend_products_request",
        trace_id=trace_id,
        article_length=len(body.article),
        question_length=len(body.question),
        k=body.k,
        product_types=body.product_types,
        customer_uuid=body.customer_uuid,
    )

    start_time = time.time()

    try:
        # Invoke agent - returns Pydantic AgentOutput
        agent_output = await agent.invoke(
            article=body.article,
            question=body.question,
            k=body.k,
            verticals=body.product_types or ["activities", "books", "articles"],
            customer_uuid=body.customer_uuid,
            trace_id=trace_id,
        )

        # Transform grouped results to API response format
        verticals_searched = body.product_types or ["activities", "books", "articles"]

        results_by_vertical = []
        for vertical in verticals_searched:
            vertical_products = agent_output.grouped_results.get(vertical, [])
            error = agent_output.errors.get(vertical)

            # Convert each product dict to ProductRecommendation
            products = [
                ProductRecommendation(
                    product_id=p["product_id"],
                    product_type=p["product_type"],
                    title=p["title"],
                    description=p.get("description"),
                    relevance_score=p["relevance_score"],
                    reasoning=agent_output.intent,  # Use intent as reasoning
                    metadata=p.get("metadata", {}),
                )
                for p in vertical_products
            ]

            results_by_vertical.append(
                VerticalResults(
                    vertical=vertical,
                    products=products,
                    count=len(products),
                    error=error,
                )
            )

        processing_time_ms = (time.time() - start_time) * 1000

        logger.info(
            "recommend_products_success",
            trace_id=trace_id,
            total_products=agent_output.total_products,
            status=agent_output.status,
            verticals_searched=verticals_searched,
            processing_time_ms=round(processing_time_ms, 2),
        )

        return RecommendProductsResponse(
            results_by_vertical=results_by_vertical,
            total_products=agent_output.total_products,
            reasoning=agent_output.intent,
            status=agent_output.status,
            verticals_searched=verticals_searched,
            trace_id=trace_id,
            processing_time_ms=round(processing_time_ms, 2),
        )

    except Exception as e:
        processing_time_ms = (time.time() - start_time) * 1000

        # Map exception to appropriate HTTP status code
        status_code, error_message = map_exception_to_http_status(e)

        logger.error(
            "recommend_products_error",
            trace_id=trace_id,
            error=str(e),
            error_type=type(e).__name__,
            status_code=status_code,
            processing_time_ms=round(processing_time_ms, 2),
            exc_info=True,
        )

        raise HTTPException(
            status_code=status_code,
            detail=error_message
            if isinstance(e, AgentException)
            else f"Failed to generate recommendations: {str(e)}",
        )
