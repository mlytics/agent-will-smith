"""Unit tests for API request/response DTOs.

Tests API boundary validation (RecommendProductsRequest, ProductRecommendation).
Focus: input validation, boundary conditions, error handling.
"""

import pytest
from pydantic import ValidationError

from agent_will_smith.app.api.product_recommendation.dto import (
    RecommendProductsRequest,
    ProductRecommendation,
)
from agent_will_smith.agent.product_recommendation.model.types import Vertical
from agent_will_smith.agent.product_recommendation.model.product import ActivityMetadata


class TestRecommendProductsRequest:
    """Tests for RecommendProductsRequest validation."""

    def test_valid_request_all_fields(
        self, valid_article: str, valid_question: str, valid_product_types: dict
    ):
        """Valid request with all required fields should pass validation."""
        request = RecommendProductsRequest(
            article=valid_article,
            question=valid_question,
            k=5,
            product_types=valid_product_types,
        )
        assert request.article == valid_article
        assert request.question == valid_question
        assert request.k == 5
        assert len(request.product_types) == 3

    def test_empty_product_types_raises_error(
        self, valid_article: str, valid_question: str
    ):
        """Empty product_types dict should raise ValueError."""
        with pytest.raises(ValidationError) as exc_info:
            RecommendProductsRequest(
                article=valid_article,
                question=valid_question,
                k=5,
                product_types={},
            )
        assert "product_types must contain at least one vertical" in str(exc_info.value)

    def test_vertical_with_empty_uuids_raises_error(
        self, valid_article: str, valid_question: str
    ):
        """Vertical with empty UUID list should raise ValueError."""
        with pytest.raises(ValidationError) as exc_info:
            RecommendProductsRequest(
                article=valid_article,
                question=valid_question,
                k=5,
                product_types={Vertical.ACTIVITIES: []},
            )
        assert "must contain at least one customer UUID" in str(exc_info.value)

    def test_article_empty_valid(
        self, valid_question: str, valid_product_types: dict
    ):
        """Empty article should pass validation (min_length=0)."""
        request = RecommendProductsRequest(
            article="",
            question=valid_question,
            k=5,
            product_types=valid_product_types,
        )
        assert request.article == ""
        assert len(request.article) == 0

    def test_article_any_length_valid(
        self, valid_question: str, valid_product_types: dict
    ):
        """Article with any length (including short strings) should pass."""
        request = RecommendProductsRequest(
            article="short",  # 5 chars
            question=valid_question,
            k=5,
            product_types=valid_product_types,
        )
        assert request.article == "short"
        assert len(request.article) == 5

    def test_single_vertical_single_uuid_valid(
        self, valid_article: str, valid_question: str
    ):
        """Single vertical with single UUID should pass (minimum valid cardinality)."""
        request = RecommendProductsRequest(
            article=valid_article,
            question=valid_question,
            k=5,
            product_types={Vertical.BOOKS: ["738c9f0b-d795-4520-979a-2b6dddc1c5a4"]},
        )
        assert len(request.product_types) == 1
        assert len(request.product_types[Vertical.BOOKS]) == 1

    def test_multiple_verticals_valid(
        self, valid_article: str, valid_question: str, valid_product_types: dict
    ):
        """Multiple verticals should pass validation."""
        request = RecommendProductsRequest(
            article=valid_article,
            question=valid_question,
            k=5,
            product_types=valid_product_types,
        )
        assert len(request.product_types) == 3

    def test_k_minimum_boundary(
        self, valid_article: str, valid_question: str, valid_product_types: dict
    ):
        """k=1 should pass (boundary: at min)."""
        request = RecommendProductsRequest(
            article=valid_article,
            question=valid_question,
            k=1,
            product_types=valid_product_types,
        )
        assert request.k == 1

    def test_k_maximum_boundary(
        self, valid_article: str, valid_question: str, valid_product_types: dict
    ):
        """k=10 should pass (boundary: at max)."""
        request = RecommendProductsRequest(
            article=valid_article,
            question=valid_question,
            k=10,
            product_types=valid_product_types,
        )
        assert request.k == 10

    def test_k_below_minimum_raises_error(
        self, valid_article: str, valid_question: str, valid_product_types: dict
    ):
        """k=0 should raise ValidationError (boundary: below min)."""
        with pytest.raises(ValidationError):
            RecommendProductsRequest(
                article=valid_article,
                question=valid_question,
                k=0,
                product_types=valid_product_types,
            )

    def test_k_above_maximum_raises_error(
        self, valid_article: str, valid_question: str, valid_product_types: dict
    ):
        """k=11 should raise ValidationError (boundary: above max)."""
        with pytest.raises(ValidationError):
            RecommendProductsRequest(
                article=valid_article,
                question=valid_question,
                k=11,
                product_types=valid_product_types,
            )


class TestProductRecommendation:
    """Tests for ProductRecommendation response model validation."""

    def test_relevance_score_at_minimum(self):
        """relevance_score=0.0 should pass (boundary: at min)."""
        rec = ProductRecommendation(
            product_id="prod-123",
            vertical=Vertical.ACTIVITIES,
            title="Test Product",
            relevance_score=0.0,
            metadata=ActivityMetadata(),
        )
        assert rec.relevance_score == 0.0

    def test_relevance_score_at_maximum(self):
        """relevance_score=1.0 should pass (boundary: at max)."""
        rec = ProductRecommendation(
            product_id="prod-123",
            vertical=Vertical.ACTIVITIES,
            title="Test Product",
            relevance_score=1.0,
            metadata=ActivityMetadata(),
        )
        assert rec.relevance_score == 1.0

    def test_relevance_score_below_minimum_raises_error(self):
        """relevance_score=-0.1 should raise ValidationError (boundary: just under min)."""
        with pytest.raises(ValidationError):
            ProductRecommendation(
                product_id="prod-123",
                vertical=Vertical.ACTIVITIES,
                title="Test Product",
                relevance_score=-0.1,
                metadata=ActivityMetadata(),
            )

    def test_relevance_score_above_maximum_raises_error(self):
        """relevance_score=1.1 should raise ValidationError (boundary: just over max)."""
        with pytest.raises(ValidationError):
            ProductRecommendation(
                product_id="prod-123",
                vertical=Vertical.ACTIVITIES,
                title="Test Product",
                relevance_score=1.1,
                metadata=ActivityMetadata(),
            )

    def test_valid_recommendation_all_fields(self):
        """Valid recommendation with all fields should pass."""
        rec = ProductRecommendation(
            product_id="act-12345",
            vertical=Vertical.ACTIVITIES,
            title="Sustainable Living Workshop",
            description="Learn eco-friendly practices",
            relevance_score=0.87,
            metadata=ActivityMetadata(
                category="environment",
                organizer="EcoLife Foundation",
            ),
        )
        assert rec.product_id == "act-12345"
        assert rec.vertical == Vertical.ACTIVITIES
        assert rec.title == "Sustainable Living Workshop"
        assert rec.description == "Learn eco-friendly practices"
        assert rec.relevance_score == 0.87
