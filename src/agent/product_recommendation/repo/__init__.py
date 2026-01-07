"""Repository layer for product recommendation agent.

Contains product-specific data access logic that wraps shared infrastructure clients.
"""

from src.agent.product_recommendation.repo.product_vector_repository import ProductVectorRepository

__all__ = ["ProductVectorRepository"]
