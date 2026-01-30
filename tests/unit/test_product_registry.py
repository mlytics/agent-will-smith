"""Unit tests for ProductRegistry business logic.

Tests availability filters, DTO class mapping, and index name resolution.
Focus: per-vertical filter logic, correct DTO class delegation.
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from agent_will_smith.agent.product_recommendation.model.product_registry import (
    ProductRegistry,
)
from agent_will_smith.agent.product_recommendation.model.types import Vertical
from agent_will_smith.agent.product_recommendation.repo.dto import (
    ActivityDTO,
    BookDTO,
    ArticleDTO,
)


class TestGetAvailabilityFilter:
    """Tests for ProductRegistry.get_availability_filter() method."""

    def test_articles_returns_is_active_filter(self, mock_config: MagicMock):
        """ARTICLES filter should return {'is_active': True}."""
        registry = ProductRegistry(mock_config)
        result = registry.get_availability_filter(Vertical.ARTICLES)
        assert result == {"is_active": True}

    def test_books_returns_is_active_filter(self, mock_config: MagicMock):
        """BOOKS filter should return {'is_active': True}."""
        registry = ProductRegistry(mock_config)
        result = registry.get_availability_filter(Vertical.BOOKS)
        assert result == {"is_active": True}

    def test_activities_returns_end_time_filter(self, mock_config: MagicMock):
        """ACTIVITIES filter should return {'end_time >': <now>}."""
        registry = ProductRegistry(mock_config)
        result = registry.get_availability_filter(Vertical.ACTIVITIES)
        assert "end_time >" in result

    def test_activities_filter_uses_utc_time(self, mock_config: MagicMock):
        """ACTIVITIES filter should use current UTC time."""
        fixed_time = datetime(2024, 6, 15, 10, 30, 0, tzinfo=timezone.utc)
        expected_time_str = "2024-06-15T10:30:00Z"

        with patch(
            "agent_will_smith.agent.product_recommendation.model.product_registry.datetime"
        ) as mock_datetime:
            mock_datetime.now.return_value = fixed_time
            mock_datetime.strftime = datetime.strftime
            # Need to ensure the format method works
            registry = ProductRegistry(mock_config)
            result = registry.get_availability_filter(Vertical.ACTIVITIES)

            # Verify datetime.now was called with UTC
            mock_datetime.now.assert_called_with(timezone.utc)
            assert result == {"end_time >": expected_time_str}


class TestGetDtoClass:
    """Tests for ProductRegistry.get_dto_class() method."""

    def test_activities_returns_activity_dto(self, mock_config: MagicMock):
        """ACTIVITIES should return ActivityDTO class."""
        registry = ProductRegistry(mock_config)
        result = registry.get_dto_class(Vertical.ACTIVITIES)
        assert result is ActivityDTO

    def test_books_returns_book_dto(self, mock_config: MagicMock):
        """BOOKS should return BookDTO class."""
        registry = ProductRegistry(mock_config)
        result = registry.get_dto_class(Vertical.BOOKS)
        assert result is BookDTO

    def test_articles_returns_article_dto(self, mock_config: MagicMock):
        """ARTICLES should return ArticleDTO class."""
        registry = ProductRegistry(mock_config)
        result = registry.get_dto_class(Vertical.ARTICLES)
        assert result is ArticleDTO


class TestGetIndexName:
    """Tests for ProductRegistry.get_index_name() method."""

    def test_activities_returns_configured_index(self, mock_config: MagicMock):
        """ACTIVITIES should return configured activities_index."""
        registry = ProductRegistry(mock_config)
        result = registry.get_index_name(Vertical.ACTIVITIES)
        assert result == "catalog.schema.activity_index"

    def test_books_returns_configured_index(self, mock_config: MagicMock):
        """BOOKS should return configured books_index."""
        registry = ProductRegistry(mock_config)
        result = registry.get_index_name(Vertical.BOOKS)
        assert result == "catalog.schema.book_index"

    def test_articles_returns_configured_index(self, mock_config: MagicMock):
        """ARTICLES should return configured articles_index."""
        registry = ProductRegistry(mock_config)
        result = registry.get_index_name(Vertical.ARTICLES)
        assert result == "catalog.schema.article_index"


class TestGetColumns:
    """Tests for ProductRegistry.get_columns() method."""

    def test_activities_delegates_to_dto(self, mock_config: MagicMock):
        """ACTIVITIES get_columns() should delegate to ActivityDTO.get_db_columns()."""
        registry = ProductRegistry(mock_config)
        result = registry.get_columns(Vertical.ACTIVITIES)
        expected = ActivityDTO.get_db_columns()
        assert result == expected

    def test_books_delegates_to_dto(self, mock_config: MagicMock):
        """BOOKS get_columns() should delegate to BookDTO.get_db_columns()."""
        registry = ProductRegistry(mock_config)
        result = registry.get_columns(Vertical.BOOKS)
        expected = BookDTO.get_db_columns()
        assert result == expected

    def test_articles_delegates_to_dto(self, mock_config: MagicMock):
        """ARTICLES get_columns() should delegate to ArticleDTO.get_db_columns()."""
        registry = ProductRegistry(mock_config)
        result = registry.get_columns(Vertical.ARTICLES)
        expected = ArticleDTO.get_db_columns()
        assert result == expected
