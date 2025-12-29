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
    )

    start_time = time.time()

    try:
        # Invoke agent (LangGraph workflow)
        agent_response = await recommend_products(
            article=body.article,
            question=body.question,
            k=body.k,
            trace_id=trace_id,
            verticals=body.product_types,  # Map product_types to verticals
            customer_uuid=None,  # TODO: Extract from auth token
        )

        # Transform grouped results to flat list for API compatibility
        products = []
        grouped_results = agent_response.get("grouped_results", {})
        
        for vertical, vertical_products in grouped_results.items():
            for product_dict in vertical_products:
                products.append(
                    ProductRecommendation(
                        product_id=product_dict["product_id"],
                        product_type=product_dict["product_type"],
                        title=product_dict["title"],
                        description=product_dict.get("description"),
                        relevance_score=product_dict["relevance_score"],
                        reasoning=agent_response.get("intent", ""),  # Use intent as reasoning
                        metadata=product_dict.get("metadata", {}),
                    )
                )

        processing_time_ms = (time.time() - start_time) * 1000

        logger.info(
            "recommend_products_success",
            trace_id=trace_id,
            products_count=len(products),
            total_by_vertical=agent_response.get("total_products", 0),
            status=agent_response.get("status", "complete"),
            processing_time_ms=round(processing_time_ms, 2),
        )

        return RecommendProductsResponse(
            products=products,
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

