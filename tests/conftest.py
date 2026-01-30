"""Shared test fixtures for all test modules."""

import pytest
from unittest.mock import MagicMock

from agent_will_smith.agent.product_recommendation.model.types import Vertical


@pytest.fixture
def valid_article() -> str:
    """Return a valid article text (min 10 characters)."""
    return "This article discusses sustainable living and eco-friendly products for modern homes."


@pytest.fixture
def valid_question() -> str:
    """Return a valid question (min 5 characters)."""
    return "What products would help someone live more sustainably?"


@pytest.fixture
def valid_product_types() -> dict[Vertical, list[str]]:
    """Return valid product_types with at least one UUID per vertical."""
    return {
        Vertical.ACTIVITIES: ["0b8ecbe2-6097-4ca8-b61b-dfeb1578b011"],
        Vertical.BOOKS: ["738c9f0b-d795-4520-979a-2b6dddc1c5a4"],
        Vertical.ARTICLES: ["0b8ecbe2-6097-4ca8-b61b-dfeb1578b011"],
    }


@pytest.fixture
def mock_config() -> MagicMock:
    """Return a mock Config with required index fields."""
    config = MagicMock()
    config.activities_index = "catalog.schema.activity_index"
    config.books_index = "catalog.schema.book_index"
    config.articles_index = "catalog.schema.article_index"
    return config
