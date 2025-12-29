"""API routes for product recommendation endpoints.

Follows guideline: "1 HTTP URL ↔ 1 agent"
Each endpoint maps to a single agent function.
"""

import time
from typing import Annotated
from fastapi import APIRouter, Depends, Request, HTTPException
import structlog

from app.middleware.auth import verify_api_key
from core.exceptions import map_exception_to_http_status, AgentException
from app.gateway.dto.schemas import (
    RecommendProductsRequest,
    RecommendProductsResponse,
    ProductRecommendation,
    VerticalResults,
)
from agent import recommend_products

logger = structlog.get_logger(__name__)

router = APIRouter()




@router.post(
    "/recommend-products",
    response_model=RecommendProductsResponse,
    summary="Recommend products based on article and question",
    description="""
    Analyzes an article and question to recommend relevant products (activities and books).
    
    Implementation:
    - Uses Databricks vector search for semantic product retrieval
    - Direct tool orchestration (LangChain, LangGraph-ready architecture)
    - LLM reasoning for selection and ranking
    
    **Architecture:** Simple and predictable flow, ready for LangGraph migration when needed.
    **Authentication:** Requires Bearer token in Authorization header.
    """,
    tags=["Recommendations"],
)
async def recommend_products_endpoint(
    request: Request,
    body: RecommendProductsRequest,
    api_key: Annotated[str, Depends(verify_api_key)],
) -> RecommendProductsResponse:
    """Recommend products endpoint - maps 1:1 to recommend_products agent.

    Args:
        request: FastAPI request (for trace_id)
        body: Request payload with article, question, and k
        api_key: Validated API key from Bearer token

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
        # Invoke agent (LangGraph workflow) - returns Pydantic AgentOutput
        agent_output = await recommend_products(
            article=body.article,
            question=body.question,
            k=body.k,
            trace_id=trace_id,
            verticals=body.product_types,  # Map product_types to verticals
            customer_uuid=body.customer_uuid,  # From request body
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
            detail=error_message if isinstance(e, AgentException) else f"Failed to generate recommendations: {str(e)}",
        )

