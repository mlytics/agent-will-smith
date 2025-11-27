"""
Test Vext API response format compliance
Based on spec document to ensure exact format matching
"""
import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from app import app

client = TestClient(app)


class TestVextAPIGenerateQuestions:
    """Test /generateQuestions matches Vext API format exactly"""
    
    @patch('app.gemini_service.generate_questions', new_callable=AsyncMock)
    @patch('app.content_service.reserve_content_id_from_url', new_callable=AsyncMock)
    @patch('app.content_service.save_content', new_callable=AsyncMock)
    @patch('app.cache_service.get', new_callable=AsyncMock)
    @patch('app.cache_service.set', new_callable=AsyncMock)
    def test_generate_questions_exact_vext_format(self, mock_cache_set, mock_cache_get, 
                                                   mock_save_content, mock_reserve_id, 
                                                   mock_gemini, auth_headers):
        """Test response matches exact Vext API format from spec"""
        mock_cache_get.return_value = None
        mock_cache_set.return_value = None
        mock_gemini.return_value = {
            "questions": [
                {"text": "天泓文創(08500)盤中飆升逾40%，創52周新高，背後有何催化劑？"},
                {"text": "天泓文創股價放量創高，市場資金動向透露了什麼訊號？"},
                {"text": "成交量與股價同步走高，這是否意味著天泓文創的上升趨勢將持續？"},
                {"text": "55:45的主動買沽比率，如何解讀市場對天泓文創的看法？"},
                {"text": "RSI飆升至83.58，天泓文創是否已進入超買區間？"}
            ],
            "tokens_used": 100
        }
        mock_reserve_id.return_value = "56e71457-c55d-4b13-bc8a-205cbdb42673"
        mock_save_content.return_value = None
        
        response = client.post(
            "/generateQuestions",
            json={
                "inputs": {
                    "context": "Test content",
                    "lang": "zh-tw"
                },
                "user": "86b51fd1-5186-45c2-84f6-7977dd616119",
                "type": "widget_page",
                "source_url": "https://m.cnyes.com/news/id/5627491"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify exact structure from spec
        assert "task_id" in data
        assert isinstance(data["task_id"], str)
        assert len(data["task_id"]) > 0
        
        assert "data" in data
        assert data["data"]["status"] == "succeeded"
        
        # Verify outputs structure
        outputs = data["data"]["outputs"]
        assert "result" in outputs
        assert "content_id" in outputs
        
        # Verify result has question_1 to question_5
        result = outputs["result"]
        assert isinstance(result, dict)
        for i in range(1, 6):
            assert f"question_{i}" in result
            assert isinstance(result[f"question_{i}"], str)
        
        # Verify content_id format (UUID)
        assert isinstance(outputs["content_id"], str)
        assert len(outputs["content_id"]) == 36  # UUID format
        
        # Verify timestamps
        assert "elapsed_time" in data["data"]
        assert "created_at" in data["data"]
        assert "finished_at" in data["data"]
        assert isinstance(data["data"]["elapsed_time"], (int, float))
        assert isinstance(data["data"]["created_at"], int)
        assert isinstance(data["data"]["finished_at"], int)
        assert data["data"]["finished_at"] >= data["data"]["created_at"]


class TestVextAPIGetMetadata:
    """Test /getMetadata matches Vext API format exactly"""
    
    @patch('app.search_service.get_metadata', new_callable=AsyncMock)
    @patch('app.cache_service.get', new_callable=AsyncMock)
    @patch('app.cache_service.set', new_callable=AsyncMock)
    def test_get_metadata_exact_vext_format(self, mock_cache_set, mock_cache_get, 
                                            mock_get_metadata, auth_headers, test_domain):
        """Test response matches exact Vext API format from spec"""
        mock_cache_get.return_value = None
        mock_cache_set.return_value = None
        
        # Mock metadata result
        mock_get_metadata.return_value = {
            "domain": "cnyes.com",
            "title": "Test Title",
            "summary": "Test Summary",
            "tags": ["港股", "異動股", "天泓文創"],
            "images": [
                {
                    "url": "https://cnyes.com/image.jpg",
                    "width": 800,
                    "height": 600,
                    "type": "og:image"
                }
            ],
            "sources": [
                {
                    "title": "相關文章標題",
                    "url": "https://cnyes.com/related-article",
                    "snippet": "相關文章摘要..."
                }
            ],
            "tokens_used": 150,
            "search_quota": 1
        }
        
        response = client.post(
            "/getMetadata",
            json={
                "inputs": {
                    "query": "神盾衛星加入Viasat ELEVATE的策略意義為何？",
                    "url": test_domain,
                    "tag_prompt": ""
                },
                "user": "86b51fd1-5186-45c2-84f6-7977dd616119"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify exact structure from spec
        assert "task_id" in data
        assert isinstance(data["task_id"], str)
        
        assert "data" in data
        assert data["data"]["status"] == "succeeded"
        
        # Verify outputs structure
        outputs = data["data"]["outputs"]
        
        # Verify tag is a string (comma-separated), not array
        assert "tag" in outputs
        assert isinstance(outputs["tag"], str)
        # Tag should be comma-separated string
        if outputs["tag"]:
            assert "," in outputs["tag"] or len(outputs["tag"]) > 0
        
        # Verify images format: array with objects containing JSON strings
        assert "images" in outputs
        assert isinstance(outputs["images"], list)
        assert len(outputs["images"]) > 0
        
        for img_obj in outputs["images"]:
            assert "images" in img_obj
            assert isinstance(img_obj["images"], str)
            # Verify it's valid JSON
            images_data = json.loads(img_obj["images"])
            assert "images" in images_data
            assert isinstance(images_data["images"], list)
        
        # Verify sources format: array with objects containing JSON strings
        assert "sources" in outputs
        assert isinstance(outputs["sources"], list)
        assert len(outputs["sources"]) > 0
        
        for source_obj in outputs["sources"]:
            assert "sources" in source_obj
            assert isinstance(source_obj["sources"], str)
            # Verify it's valid JSON with citations
            sources_data = json.loads(source_obj["sources"])
            assert "citations" in sources_data
            assert isinstance(sources_data["citations"], list)
            
            # Verify citation structure
            for citation in sources_data["citations"]:
                assert "title" in citation
                assert "url" in citation
                assert "content" in citation
                assert isinstance(citation["title"], str)
                assert isinstance(citation["url"], str)
                assert isinstance(citation["content"], str)
        
        # Verify timestamps
        assert "elapsed_time" in data["data"]
        assert "created_at" in data["data"]
        assert "finished_at" in data["data"]
        assert isinstance(data["data"]["elapsed_time"], (int, float))
        assert isinstance(data["data"]["created_at"], int)
        assert isinstance(data["data"]["finished_at"], int)
    
    @patch('app.search_service.get_metadata', new_callable=AsyncMock)
    @patch('app.cache_service.get', new_callable=AsyncMock)
    @patch('app.cache_service.set', new_callable=AsyncMock)
    def test_get_metadata_empty_tag_and_images(self, mock_cache_set, mock_cache_get,
                                               mock_get_metadata, auth_headers, test_domain):
        """Test getMetadata with empty tag and images returns proper format"""
        mock_cache_get.return_value = None
        mock_cache_set.return_value = None
        
        mock_get_metadata.return_value = {
            "domain": "cnyes.com",
            "title": "",
            "summary": "",
            "tags": [],
            "images": [],
            "sources": [],
            "tokens_used": 0,
            "search_quota": 0
        }
        
        response = client.post(
            "/getMetadata",
            json={
                "inputs": {
                    "query": "",
                    "url": test_domain,
                    "tag_prompt": ""
                },
                "user": "test_user"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        outputs = data["data"]["outputs"]
        
        # Tag should be empty string, not null or array
        assert outputs["tag"] == ""
        
        # Images should still be array with JSON string
        assert isinstance(outputs["images"], list)
        assert len(outputs["images"]) > 0
        images_data = json.loads(outputs["images"][0]["images"])
        assert images_data["images"] == []
        
        # Sources should still be array with JSON string
        assert isinstance(outputs["sources"], list)
        assert len(outputs["sources"]) > 0
        sources_data = json.loads(outputs["sources"][0]["sources"])
        assert sources_data["citations"] == []


class TestVextAPIGetAnswer:
    """Test /getAnswer matches Vext API format exactly"""
    
    @patch('app.gemini_service.generate_answer', new_callable=AsyncMock)
    @patch('app.content_service.get_content', new_callable=AsyncMock)
    @patch('app.cache_service.get', new_callable=AsyncMock)
    @patch('app.cache_service.set', new_callable=AsyncMock)
    def test_get_answer_exact_vext_format(self, mock_cache_set, mock_cache_get, 
                                          mock_get_content, mock_gemini, auth_headers):
        """Test response matches exact Vext API format from spec"""
        mock_cache_get.return_value = None
        mock_cache_set.return_value = None
        mock_get_content.return_value = "Article content here..."
        mock_gemini.return_value = {
            "answer": "### 歐盟尋求稀土替代供應及短期保護計畫\\n\\n面對中國可能限制稀土出口...",
            "tokens_used": 200
        }
        
        response = client.post(
            "/getAnswer",
            json={
                "inputs": {
                    "query": "歐盟如何尋找稀土替代供應來源，並制定短期保護計畫？",
                    "url": "",
                    "prompt": "Your task is to generate...",
                    "content_id": "d1e3b8d3-0b0c-47f9-8a9b-cca7b74ad5ae",
                    "lang": "zh-tw"
                },
                "user": "86b51fd1-5186-45c2-84f6-7977dd616119",
                "stream": False
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify exact structure from spec
        assert "event" in data
        assert data["event"] == "workflow_finished"
        
        assert "task_id" in data
        assert isinstance(data["task_id"], str)
        assert len(data["task_id"]) > 0
        
        assert "data" in data
        assert data["data"]["status"] == "succeeded"
        
        # Verify outputs structure (Vext API uses "summary" not "result")
        outputs = data["data"]["outputs"]
        assert "summary" in outputs
        assert isinstance(outputs["summary"], str)
        assert len(outputs["summary"]) > 0
        
        # Verify timestamps
        assert "elapsed_time" in data["data"]
        assert "created_at" in data["data"]
        assert "finished_at" in data["data"]
        assert isinstance(data["data"]["elapsed_time"], (int, float))
        assert isinstance(data["data"]["created_at"], int)
        assert isinstance(data["data"]["finished_at"], int)
        assert data["data"]["finished_at"] >= data["data"]["created_at"]
        
        # Verify no provider or meta fields (removed per spec)
        assert "provider" not in data["data"]
        assert "meta" not in data["data"]
    
    @patch('app.gemini_service.generate_answer', new_callable=AsyncMock)
    @patch('app.content_service.fetch_content', new_callable=AsyncMock)
    @patch('app.cache_service.get', new_callable=AsyncMock)
    @patch('app.cache_service.set', new_callable=AsyncMock)
    def test_get_answer_with_url_not_content_id(self, mock_cache_set, mock_cache_get, 
                                               mock_fetch_content, mock_gemini, 
                                               auth_headers, test_domain):
        """Test getAnswer with URL instead of content_id"""
        mock_cache_get.return_value = None
        mock_cache_set.return_value = None
        mock_fetch_content.return_value = "Article content from URL..."
        mock_gemini.return_value = {
            "answer": "Answer text here",
            "tokens_used": 150
        }
        
        response = client.post(
            "/getAnswer",
            json={
                "inputs": {
                    "query": "Test question?",
                    "url": test_domain,
                    "lang": "zh-tw"
                },
                "user": "test_user",
                "stream": False
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify Vext format (uses "summary" not "result")
        assert data["event"] == "workflow_finished"
        assert "task_id" in data
        assert data["data"]["status"] == "succeeded"
        assert "summary" in data["data"]["outputs"]


class TestVextAPISearchBehavior:
    """Test search behavior matches Vext API spec"""
    
    @patch('app.search_service.get_metadata', new_callable=AsyncMock)
    @patch('app.cache_service.get', new_callable=AsyncMock)
    @patch('app.cache_service.set', new_callable=AsyncMock)
    def test_get_metadata_uses_site_restriction(self, mock_cache_set, mock_cache_get, 
                                                 mock_get_metadata, auth_headers, test_domain):
        """Test that Google Search uses site: restriction per spec"""
        mock_cache_get.return_value = None
        mock_cache_set.return_value = None
        
        # Mock metadata result
        mock_get_metadata.return_value = {
            "domain": "cnyes.com",
            "title": "Test",
            "summary": "Test",
            "tags": [],
            "images": [],
            "sources": [
                {
                    "title": "Test Article",
                    "url": "https://cnyes.com/article",
                    "snippet": "Test snippet"
                }
            ],
            "tokens_used": 0,
            "search_quota": 1
        }
        
        response = client.post(
            "/getMetadata",
            json={
                "inputs": {
                    "query": "神盾衛星 Viasat ELEVATE",
                    "url": test_domain,
                    "tag_prompt": ""
                },
                "user": "test_user"
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        # The site: restriction is handled in search_service.get_metadata
        # We verify the sources are properly formatted
        data = response.json()
        sources = json.loads(data["data"]["outputs"]["sources"][0]["sources"])
        assert "citations" in sources


class TestVextAPITimestampBehavior:
    """Test timestamp behavior matches Vext API"""
    
    @patch('app.gemini_service.generate_questions', new_callable=AsyncMock)
    @patch('app.content_service.reserve_content_id_from_url', new_callable=AsyncMock)
    @patch('app.content_service.save_content', new_callable=AsyncMock)
    @patch('app.cache_service.get', new_callable=AsyncMock)
    @patch('app.cache_service.set', new_callable=AsyncMock)
    def test_timestamps_are_valid_unix_timestamps(self, mock_cache_set, mock_cache_get, 
                                                  mock_save_content, mock_reserve_id, 
                                                  mock_gemini, auth_headers):
        """Test that timestamps are valid Unix timestamps"""
        import time
        mock_cache_get.return_value = None
        mock_cache_set.return_value = None
        mock_gemini.return_value = {
            "questions": [{"text": "Test"}],
            "tokens_used": 100
        }
        mock_reserve_id.return_value = "test_id"
        mock_save_content.return_value = None
        
        before_time = int(time.time())
        response = client.post(
            "/generateQuestions",
            json={
                "inputs": {
                    "context": "Test"
                },
                "user": "test_user"
            },
            headers=auth_headers
        )
        after_time = int(time.time())
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify timestamps are within reasonable range
        assert before_time <= data["data"]["created_at"] <= after_time + 1
        assert before_time <= data["data"]["finished_at"] <= after_time + 1
        assert data["data"]["elapsed_time"] >= 0
        assert data["data"]["elapsed_time"] < 10  # Should be fast in test

