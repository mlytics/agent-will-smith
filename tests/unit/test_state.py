"""Unit tests for AgentInput state helpers.

Tests verticals property and get_customer_uuids() method.
Focus: state helper methods, cardinality edge cases.
"""

import pytest

from agent_will_smith.agent.product_recommendation.state import AgentInput
from agent_will_smith.agent.product_recommendation.model.types import Vertical


class TestAgentInputVerticals:
    """Tests for AgentInput.verticals property."""

    def test_verticals_returns_keys_from_product_types(self):
        """verticals should return keys from product_types dict."""
        agent_input = AgentInput(
            article="Test article with enough characters",
            question="Test question here",
            k=5,
            product_types={
                Vertical.ACTIVITIES: ["uuid-1"],
                Vertical.BOOKS: ["uuid-2"],
            },
        )
        verticals = agent_input.verticals
        assert set(verticals) == {Vertical.ACTIVITIES, Vertical.BOOKS}

    def test_verticals_with_single_vertical(self):
        """verticals should work with single vertical (cardinality: one)."""
        agent_input = AgentInput(
            article="Test article with enough characters",
            question="Test question here",
            k=5,
            product_types={Vertical.ARTICLES: ["uuid-1"]},
        )
        verticals = agent_input.verticals
        assert verticals == [Vertical.ARTICLES]

    def test_verticals_with_all_verticals(self):
        """verticals should work with all three verticals (cardinality: max)."""
        agent_input = AgentInput(
            article="Test article with enough characters",
            question="Test question here",
            k=5,
            product_types={
                Vertical.ACTIVITIES: ["uuid-1"],
                Vertical.BOOKS: ["uuid-2"],
                Vertical.ARTICLES: ["uuid-3"],
            },
        )
        verticals = agent_input.verticals
        assert len(verticals) == 3
        assert set(verticals) == {Vertical.ACTIVITIES, Vertical.BOOKS, Vertical.ARTICLES}


class TestAgentInputGetCustomerUuids:
    """Tests for AgentInput.get_customer_uuids() method."""

    def test_get_customer_uuids_for_existing_vertical(self):
        """get_customer_uuids() should return UUIDs for existing vertical."""
        agent_input = AgentInput(
            article="Test article with enough characters",
            question="Test question here",
            k=5,
            product_types={
                Vertical.ACTIVITIES: ["uuid-1", "uuid-2"],
                Vertical.BOOKS: ["uuid-3"],
            },
        )
        uuids = agent_input.get_customer_uuids(Vertical.ACTIVITIES)
        assert uuids == ["uuid-1", "uuid-2"]

    def test_get_customer_uuids_for_missing_vertical_returns_empty_list(self):
        """get_customer_uuids() should return empty list for missing vertical."""
        agent_input = AgentInput(
            article="Test article with enough characters",
            question="Test question here",
            k=5,
            product_types={Vertical.ACTIVITIES: ["uuid-1"]},
        )
        uuids = agent_input.get_customer_uuids(Vertical.BOOKS)
        assert uuids == []

    def test_get_customer_uuids_single_uuid(self):
        """get_customer_uuids() should work with single UUID."""
        agent_input = AgentInput(
            article="Test article with enough characters",
            question="Test question here",
            k=5,
            product_types={Vertical.BOOKS: ["single-uuid"]},
        )
        uuids = agent_input.get_customer_uuids(Vertical.BOOKS)
        assert uuids == ["single-uuid"]

    def test_get_customer_uuids_multiple_uuids(self):
        """get_customer_uuids() should work with multiple UUIDs."""
        agent_input = AgentInput(
            article="Test article with enough characters",
            question="Test question here",
            k=5,
            product_types={
                Vertical.ARTICLES: ["uuid-a", "uuid-b", "uuid-c"],
            },
        )
        uuids = agent_input.get_customer_uuids(Vertical.ARTICLES)
        assert uuids == ["uuid-a", "uuid-b", "uuid-c"]
