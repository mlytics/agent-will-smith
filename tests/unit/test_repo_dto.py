"""Unit tests for repository DTOs (Databricks vector search results).

Tests DTO transformations and score validation constraints.
Focus: to_product_result() mappings, score boundaries, get_db_columns().
"""

import pytest
from pydantic import ValidationError

from agent_will_smith.agent.product_recommendation.repo.dto import (
    ActivityDTO,
    BookDTO,
    ArticleDTO,
    VectorSearchDTO,
)
from agent_will_smith.agent.product_recommendation.model.types import Vertical


class TestActivityDTO:
    """Tests for ActivityDTO transformation and validation."""

    def test_to_product_result_maps_content_id_to_product_id(self):
        """content_id should map to product_id in ProductResult."""
        dto = ActivityDTO(
            content_id="act-12345",
            title="Workshop",
            score=0.85,
        )
        result = dto.to_product_result(Vertical.ACTIVITIES)
        assert result.product_id == "act-12345"

    def test_to_product_result_maps_score_to_relevance_score(self):
        """score should map to relevance_score in ProductResult."""
        dto = ActivityDTO(
            content_id="act-12345",
            title="Workshop",
            score=0.92,
        )
        result = dto.to_product_result(Vertical.ACTIVITIES)
        assert result.relevance_score == 0.92

    def test_to_product_result_maps_title(self):
        """title should map directly to title in ProductResult."""
        dto = ActivityDTO(
            content_id="act-12345",
            title="Sustainable Living Workshop",
            score=0.85,
        )
        result = dto.to_product_result(Vertical.ACTIVITIES)
        assert result.title == "Sustainable Living Workshop"

    def test_to_product_result_maps_description(self):
        """description should map directly to description in ProductResult."""
        dto = ActivityDTO(
            content_id="act-12345",
            title="Workshop",
            description="Learn eco-friendly practices",
            score=0.85,
        )
        result = dto.to_product_result(Vertical.ACTIVITIES)
        assert result.description == "Learn eco-friendly practices"

    def test_to_product_result_sets_vertical(self):
        """vertical should be set from parameter."""
        dto = ActivityDTO(
            content_id="act-12345",
            title="Workshop",
            score=0.85,
        )
        result = dto.to_product_result(Vertical.ACTIVITIES)
        assert result.vertical == Vertical.ACTIVITIES

    def test_to_product_result_with_all_optional_fields_null(self):
        """DTO with all optional fields null should still transform correctly."""
        dto = ActivityDTO(
            content_id="act-12345",
            title="Workshop",
        )
        result = dto.to_product_result(Vertical.ACTIVITIES)
        assert result.product_id == "act-12345"
        assert result.description is None
        assert result.metadata.category is None
        assert result.metadata.organizer is None
        assert result.metadata.location_name is None

    def test_to_product_result_maps_metadata_fields(self):
        """Activity-specific metadata fields should be mapped correctly."""
        dto = ActivityDTO(
            content_id="act-12345",
            title="Workshop",
            score=0.85,
            category="environment",
            organizer="EcoLife Foundation",
            location_name="Green Community Center",
            location_address="123 Eco St",
            start_time="2024-03-15T10:00:00Z",
            end_time="2024-03-15T12:00:00Z",
            permalink_url="https://example.com/act/123",
            cover_image_urls=["https://example.com/img1.jpg"],
        )
        result = dto.to_product_result(Vertical.ACTIVITIES)
        assert result.metadata.category == "environment"
        assert result.metadata.organizer == "EcoLife Foundation"
        assert result.metadata.location_name == "Green Community Center"
        assert result.metadata.location_address == "123 Eco St"
        assert result.metadata.start_time == "2024-03-15T10:00:00Z"
        assert result.metadata.end_time == "2024-03-15T12:00:00Z"
        assert result.metadata.permalink_url == "https://example.com/act/123"
        assert result.metadata.cover_image_urls == ["https://example.com/img1.jpg"]

    def test_score_at_minimum_boundary(self):
        """score=0.0 should pass validation (boundary: at min)."""
        dto = ActivityDTO(
            content_id="act-12345",
            title="Workshop",
            score=0.0,
        )
        assert dto.score == 0.0

    def test_score_at_maximum_boundary(self):
        """score=1.0 should pass validation (boundary: at max)."""
        dto = ActivityDTO(
            content_id="act-12345",
            title="Workshop",
            score=1.0,
        )
        assert dto.score == 1.0

    def test_score_below_minimum_raises_error(self):
        """score=-0.01 should raise ValidationError (boundary: just under min)."""
        with pytest.raises(ValidationError):
            ActivityDTO(
                content_id="act-12345",
                title="Workshop",
                score=-0.01,
            )

    def test_score_above_maximum_raises_error(self):
        """score=1.01 should raise ValidationError (boundary: just over max)."""
        with pytest.raises(ValidationError):
            ActivityDTO(
                content_id="act-12345",
                title="Workshop",
                score=1.01,
            )


class TestBookDTO:
    """Tests for BookDTO transformation and validation."""

    def test_to_product_result_maps_title_main_to_title(self):
        """title_main should map to title in ProductResult (special mapping)."""
        dto = BookDTO(
            content_id="book-67890",
            title_main="The Sustainable Home",
            score=0.78,
        )
        result = dto.to_product_result(Vertical.BOOKS)
        assert result.title == "The Sustainable Home"

    def test_to_product_result_maps_content_id_to_product_id(self):
        """content_id should map to product_id."""
        dto = BookDTO(
            content_id="book-67890",
            title_main="Book Title",
            score=0.78,
        )
        result = dto.to_product_result(Vertical.BOOKS)
        assert result.product_id == "book-67890"

    def test_to_product_result_with_empty_authors_list(self):
        """Empty authors list should be valid (cardinality: zero elements)."""
        dto = BookDTO(
            content_id="book-67890",
            title_main="Book Title",
            authors=[],
            score=0.78,
        )
        result = dto.to_product_result(Vertical.BOOKS)
        assert result.metadata.authors == []

    def test_to_product_result_maps_metadata_fields(self):
        """Book-specific metadata fields should be mapped correctly."""
        dto = BookDTO(
            content_id="book-67890",
            title_main="The Sustainable Home",
            title_subtitle="A Guide to Eco-Friendly Living",
            description="Comprehensive guide...",
            authors=["Jane Smith", "John Doe"],
            categories=["Environment", "Lifestyle"],
            permalink_url="https://example.com/books/123",
            cover_image_url="https://example.com/covers/book.jpg",
            prices=["$19.99", "$9.99 (ebook)"],
            score=0.78,
        )
        result = dto.to_product_result(Vertical.BOOKS)
        assert result.metadata.title_subtitle == "A Guide to Eco-Friendly Living"
        assert result.metadata.authors == ["Jane Smith", "John Doe"]
        assert result.metadata.categories == ["Environment", "Lifestyle"]
        assert result.metadata.permalink_url == "https://example.com/books/123"
        assert result.metadata.cover_image_url == "https://example.com/covers/book.jpg"
        assert result.metadata.prices == ["$19.99", "$9.99 (ebook)"]

    def test_score_at_minimum_boundary(self):
        """score=0.0 should pass validation (boundary: at min)."""
        dto = BookDTO(
            content_id="book-67890",
            title_main="Book",
            score=0.0,
        )
        assert dto.score == 0.0

    def test_score_at_maximum_boundary(self):
        """score=1.0 should pass validation (boundary: at max)."""
        dto = BookDTO(
            content_id="book-67890",
            title_main="Book",
            score=1.0,
        )
        assert dto.score == 1.0

    def test_score_below_minimum_raises_error(self):
        """score=-0.01 should raise ValidationError."""
        with pytest.raises(ValidationError):
            BookDTO(
                content_id="book-67890",
                title_main="Book",
                score=-0.01,
            )

    def test_score_above_maximum_raises_error(self):
        """score=1.01 should raise ValidationError."""
        with pytest.raises(ValidationError):
            BookDTO(
                content_id="book-67890",
                title_main="Book",
                score=1.01,
            )


class TestArticleDTO:
    """Tests for ArticleDTO transformation and validation."""

    def test_to_product_result_maps_content_to_description(self):
        """content should map to description in ProductResult (special mapping)."""
        dto = ArticleDTO(
            content_id="article-11223",
            title="10 Ways to Live Sustainably",
            content="Sustainable living starts with small changes...",
            score=0.91,
        )
        result = dto.to_product_result(Vertical.ARTICLES)
        assert result.description == "Sustainable living starts with small changes..."

    def test_to_product_result_maps_title(self):
        """title should map directly to title."""
        dto = ArticleDTO(
            content_id="article-11223",
            title="10 Ways to Live Sustainably",
            score=0.91,
        )
        result = dto.to_product_result(Vertical.ARTICLES)
        assert result.title == "10 Ways to Live Sustainably"

    def test_to_product_result_maps_content_id_to_product_id(self):
        """content_id should map to product_id."""
        dto = ArticleDTO(
            content_id="article-11223",
            title="Article Title",
            score=0.91,
        )
        result = dto.to_product_result(Vertical.ARTICLES)
        assert result.product_id == "article-11223"

    def test_to_product_result_maps_metadata_fields(self):
        """Article-specific metadata fields should be mapped correctly."""
        dto = ArticleDTO(
            content_id="article-11223",
            title="10 Ways to Live Sustainably",
            content="Content here...",
            authors=["Sarah Green"],
            keywords=["sustainability", "eco-friendly"],
            categories=["Environment", "Lifestyle"],
            permalink_url="https://example.com/articles/123",
            thumbnail_url="https://example.com/thumbs/article.jpg",
            main_image_url="https://example.com/images/article.jpg",
            publish_time="2024-01-15T08:00:00Z",
            score=0.91,
        )
        result = dto.to_product_result(Vertical.ARTICLES)
        assert result.metadata.authors == ["Sarah Green"]
        assert result.metadata.keywords == ["sustainability", "eco-friendly"]
        assert result.metadata.categories == ["Environment", "Lifestyle"]
        assert result.metadata.permalink_url == "https://example.com/articles/123"
        assert result.metadata.thumbnail_url == "https://example.com/thumbs/article.jpg"
        assert result.metadata.main_image_url == "https://example.com/images/article.jpg"
        assert result.metadata.publish_time == "2024-01-15T08:00:00Z"

    def test_score_at_minimum_boundary(self):
        """score=0.0 should pass validation (boundary: at min)."""
        dto = ArticleDTO(
            content_id="article-11223",
            title="Article",
            score=0.0,
        )
        assert dto.score == 0.0

    def test_score_at_maximum_boundary(self):
        """score=1.0 should pass validation (boundary: at max)."""
        dto = ArticleDTO(
            content_id="article-11223",
            title="Article",
            score=1.0,
        )
        assert dto.score == 1.0

    def test_score_below_minimum_raises_error(self):
        """score=-0.01 should raise ValidationError."""
        with pytest.raises(ValidationError):
            ArticleDTO(
                content_id="article-11223",
                title="Article",
                score=-0.01,
            )

    def test_score_above_maximum_raises_error(self):
        """score=1.01 should raise ValidationError."""
        with pytest.raises(ValidationError):
            ArticleDTO(
                content_id="article-11223",
                title="Article",
                score=1.01,
            )


class TestVectorSearchDTOGetDbColumns:
    """Tests for VectorSearchDTO.get_db_columns() method."""

    def test_activity_dto_excludes_score_from_columns(self):
        """ActivityDTO.get_db_columns() should exclude 'score' from columns."""
        columns = ActivityDTO.get_db_columns()
        assert "score" not in columns
        assert "content_id" in columns
        assert "title" in columns

    def test_book_dto_excludes_score_from_columns(self):
        """BookDTO.get_db_columns() should exclude 'score' from columns."""
        columns = BookDTO.get_db_columns()
        assert "score" not in columns
        assert "content_id" in columns
        assert "title_main" in columns

    def test_article_dto_excludes_score_from_columns(self):
        """ArticleDTO.get_db_columns() should exclude 'score' from columns."""
        columns = ArticleDTO.get_db_columns()
        assert "score" not in columns
        assert "content_id" in columns
        assert "title" in columns
        assert "content" in columns

    def test_activity_dto_returns_all_db_columns(self):
        """ActivityDTO.get_db_columns() should return all DB fields."""
        columns = ActivityDTO.get_db_columns()
        expected = [
            "content_id",
            "title",
            "description",
            "category",
            "location_name",
            "location_address",
            "organizer",
            "start_time",
            "end_time",
            "permalink_url",
            "cover_image_urls",
        ]
        assert set(columns) == set(expected)

    def test_book_dto_returns_all_db_columns(self):
        """BookDTO.get_db_columns() should return all DB fields."""
        columns = BookDTO.get_db_columns()
        expected = [
            "content_id",
            "title_main",
            "title_subtitle",
            "description",
            "authors",
            "categories",
            "permalink_url",
            "cover_image_url",
            "prices",
        ]
        assert set(columns) == set(expected)

    def test_article_dto_returns_all_db_columns(self):
        """ArticleDTO.get_db_columns() should return all DB fields."""
        columns = ArticleDTO.get_db_columns()
        expected = [
            "content_id",
            "title",
            "content",
            "authors",
            "keywords",
            "categories",
            "permalink_url",
            "thumbnail_url",
            "main_image_url",
            "publish_time",
        ]
        assert set(columns) == set(expected)
