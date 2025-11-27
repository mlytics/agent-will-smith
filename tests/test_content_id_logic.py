"""
Test content_id logic - session ID behavior
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
from app import app

client = TestClient(app)

class TestContentIDLogic:
    """Test content_id session behavior"""
    
    @patch('app.gemini_service.generate_questions', new_callable=AsyncMock)
    @patch('app.content_service.reserve_content_id_from_url', new_callable=AsyncMock)
    @patch('app.content_service.save_content', new_callable=AsyncMock)
    @patch('app.cache_service.get', new_callable=AsyncMock)
    @patch('app.cache_service.set', new_callable=AsyncMock)
    def test_content_id_generated_and_saved(self, mock_cache_set, mock_cache_get, mock_save_content, mock_reserve_id, mock_gemini, auth_headers):
        """Test that content_id is generated and content is saved"""
        mock_cache_get.return_value = None
        mock_cache_set.return_value = None
        mock_gemini.return_value = {
            "questions": [{"text": "Test"}],
            "tokens_used": 100
        }
        mock_reserve_id.return_value = "generated_content_id"
        mock_save_content.return_value = None
        
        response = client.post(
            "/generateQuestions",
            json={
                "inputs": {
                    "context": "Test content to save"
                },
                "user": "test_user"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check content_id is in response
        assert "content_id" in data["data"]["outputs"]
        content_id = data["data"]["outputs"]["content_id"]
        assert content_id == "generated_content_id"
        
        # Check content was saved with content_id
        mock_save_content.assert_called_once()
        call_args = mock_save_content.call_args
        assert call_args[0][0] == content_id  # content_id
        assert call_args[0][1] == "Test content to save"  # content
    
    @patch('app.gemini_service.generate_answer', new_callable=AsyncMock)
    @patch('app.content_service.get_content', new_callable=AsyncMock)
    @patch('app.cache_service.get', new_callable=AsyncMock)
    @patch('app.cache_service.set', new_callable=AsyncMock)
    def test_get_answer_with_content_id_retrieves_saved_content(self, mock_cache_set, mock_cache_get, mock_get_content, mock_gemini, auth_headers):
        """Test that getAnswer with content_id retrieves previously saved content"""
        mock_cache_get.return_value = None
        mock_cache_set.return_value = None
        mock_get_content.return_value = "Previously saved content"
        mock_gemini.return_value = {
            "answer": "Generated answer",
            "tokens_used": 100
        }
        
        response = client.post(
            "/getAnswer",
            json={
                "inputs": {
                    "query": "Test question",
                    "content_id": "existing_content_id"
                },
                "user": "test_user"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        
        # Should retrieve content by content_id
        mock_get_content.assert_called_once_with("existing_content_id")
        
        # Should use retrieved content for answer generation
        call_args = mock_gemini.call_args
        assert call_args[1]["content"] == "Previously saved content"
    
    @patch('app.gemini_service.generate_answer', new_callable=AsyncMock)
    @patch('app.content_service.fetch_content', new_callable=AsyncMock)
    @patch('app.cache_service.get', new_callable=AsyncMock)
    @patch('app.cache_service.set', new_callable=AsyncMock)
    def test_get_answer_without_content_id_fetches_from_url(self, mock_cache_set, mock_cache_get, mock_fetch_content, mock_gemini, auth_headers, test_domain):
        """Test that getAnswer without content_id fetches from URL"""
        mock_cache_get.return_value = None
        mock_cache_set.return_value = None
        mock_fetch_content.return_value = "Fetched from URL"
        mock_gemini.return_value = {
            "answer": "Generated answer",
            "tokens_used": 100
        }
        
        response = client.post(
            "/getAnswer",
            json={
                "inputs": {
                    "query": "Test question",
                    "url": test_domain
                },
                "user": "test_user"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        
        # Should fetch from URL
        mock_fetch_content.assert_called_once_with(test_domain)
    
    @patch('app.gemini_service.generate_questions', new_callable=AsyncMock)
    @patch('app.content_service.reserve_content_id_from_url', new_callable=AsyncMock)
    @patch('app.content_service.save_content', new_callable=AsyncMock)
    @patch('app.cache_service.get', new_callable=AsyncMock)
    @patch('app.cache_service.set', new_callable=AsyncMock)
    def test_content_id_from_url_deterministic(self, mock_cache_set, mock_cache_get, mock_save_content, mock_reserve_id, mock_gemini, auth_headers, test_domain):
        """Test that content_id generated from URL is deterministic"""
        mock_cache_get.return_value = None
        mock_cache_set.return_value = None
        mock_gemini.return_value = {
            "questions": [{"text": "Test"}],
            "tokens_used": 100
        }
        
        # Mock reserve_content_id_from_url to return deterministic hash
        import hashlib
        expected_content_id = hashlib.sha256(test_domain.encode()).hexdigest()
        mock_reserve_id.return_value = expected_content_id
        mock_save_content.return_value = None
        
        response = client.post(
            "/generateQuestions",
            json={
                "inputs": {
                    "url": test_domain
                },
                "user": "test_user"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        content_id = response.json()["data"]["outputs"]["content_id"]
        assert content_id == expected_content_id
    
    @patch('app.gemini_service.generate_answer', new_callable=AsyncMock)
    @patch('app.content_service.get_content', new_callable=AsyncMock)
    @patch('app.cache_service.get', new_callable=AsyncMock)
    @patch('app.cache_service.set', new_callable=AsyncMock)
    def test_content_id_not_found_returns_empty(self, mock_cache_set, mock_cache_get, mock_get_content, mock_gemini, auth_headers):
        """Test that when content_id is not found, returns failed status"""
        mock_cache_get.return_value = None
        mock_cache_set.return_value = None
        mock_get_content.return_value = ""  # Not found
        mock_gemini.return_value = {
            "answer": "Generated answer",
            "tokens_used": 100
        }
        
        response = client.post(
            "/getAnswer",
            json={
                "inputs": {
                    "query": "Test question",
                    "content_id": "non_existent_id"
                },
                "user": "test_user"
            },
            headers=auth_headers
        )
        
        # Should return failed status when content_id not found
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["status"] == "failed"
        assert data["data"]["outputs"] == {}
        # Gemini should not be called when content_id is not found
        mock_gemini.assert_not_called()
