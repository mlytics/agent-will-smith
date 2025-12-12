"""Test suite for API endpoints.

Run with: pytest tests/test_api.py
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import app
from agent.schemas import AgentResponse, ProductResult

client = TestClient(app)


@pytest.fixture
def mock_agent_response():
    """Mock agent response for testing."""
    return AgentResponse(
        products=[
            ProductResult(
                product_id="test-activity-1",
                product_type="activity",
                title="Test Activity",
                description="A test activity description",
                relevance_score=0.95,
                metadata={"category": "test", "location_name": "Test Location"},
            ),
            ProductResult(
                product_id="test-book-1",
                product_type="book",
                title="Test Book",
                description="A test book description",
                relevance_score=0.88,
                metadata={"authors": ["Test Author"], "publisher": "Test Publisher"},
            ),
        ],
        reasoning="These products were selected based on the test article content.",
        total_searched=2,
    )


def test_health_endpoint():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "timestamp" in data


def test_readiness_endpoint():
    """Test readiness check endpoint."""
    response = client.get("/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_metrics_endpoint():
    """Test metrics endpoint."""
    response = client.get("/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "metrics" in data
    assert "cpu_percent" in data["metrics"]
    assert "memory_mb" in data["metrics"]


@patch("app.api.routes.recommend_products")
def test_recommend_products_success(mock_recommend, mock_agent_response):
    """Test successful product recommendation request."""
    mock_recommend.return_value = mock_agent_response

    response = client.post(
        "/api/v1/recommend-products",
        headers={"Authorization": "Bearer dev-api-key-replace-in-production"},
        json={
            "article": "This is a test article about sustainable living.",
            "question": "What products would help with sustainability?",
            "k": 2,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "products" in data
    assert len(data["products"]) == 2
    assert "trace_id" in data
    assert "processing_time_ms" in data


def test_recommend_products_auth_required():
    """Test that authentication is required."""
    response = client.post(
        "/api/v1/recommend-products",
        json={
            "article": "Test article",
            "question": "Test question?",
            "k": 1,
        },
    )

    assert response.status_code == 403  # Forbidden without auth


def test_recommend_products_invalid_api_key():
    """Test that invalid API key is rejected."""
    response = client.post(
        "/api/v1/recommend-products",
        headers={"Authorization": "Bearer invalid-key"},
        json={
            "article": "Test article",
            "question": "Test question?",
            "k": 1,
        },
    )

    assert response.status_code == 401  # Unauthorized


def test_recommend_products_validation_errors():
    """Test request validation."""
    # Missing required fields
    response = client.post(
        "/api/v1/recommend-products",
        headers={"Authorization": "Bearer dev-api-key-replace-in-production"},
        json={},
    )
    assert response.status_code == 422  # Unprocessable Entity

    # Invalid k value (too high)
    response = client.post(
        "/api/v1/recommend-products",
        headers={"Authorization": "Bearer dev-api-key-replace-in-production"},
        json={"article": "Test", "question": "Test?", "k": 100},
    )
    assert response.status_code == 422

    # Article too short
    response = client.post(
        "/api/v1/recommend-products",
        headers={"Authorization": "Bearer dev-api-key-replace-in-production"},
        json={"article": "short", "question": "Test?", "k": 1},
    )
    assert response.status_code == 422

