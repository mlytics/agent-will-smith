#!/usr/bin/env python3
"""
API Server Test Script
Tests all endpoints of the AIGC MVP API Server
"""

import requests
import json
import sys
from typing import Dict, Any

# Configuration
API_BASE_URL = "http://localhost:8888"
TIMEOUT = 30

def print_section(title: str):
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def print_response(response: requests.Response, show_body: bool = True):
    """Print formatted response information"""
    print(f"Status: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    if show_body:
        try:
            body = response.json()
            print(f"Response Body (formatted):")
            print(json.dumps(body, indent=2, ensure_ascii=False))
        except:
            print(f"Response Body (raw): {response.text[:200]}...")
    print()

def test_health_check() -> bool:
    """Test the health check endpoint"""
    print_section("Testing Health Check")
    
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=TIMEOUT)
        print_response(response)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "healthy":
                print("✅ Health check passed!")
                return True
            else:
                print("❌ Health check failed: status not 'healthy'")
                return False
        else:
            print(f"❌ Health check failed: status code {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_generate_questions() -> bool:
    """Test the generateQuestions endpoint"""
    print_section("Testing Generate Questions")
    
    payload = {
        "inputs": {
            "url": "https://example.com/article",
            "context": "This is a test article about artificial intelligence and machine learning.",
            "lang": "zh-tw"
        },
        "user": "test_user",
        "type": "answer_page"
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/generateQuestions",
            json=payload,
            timeout=TIMEOUT
        )
        print(f"Request payload:")
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        print("\nResponse:")
        print_response(response)
        
        if response.status_code == 200:
            data = response.json()
            if "data" in data and "outputs" in data["data"]:
                print("✅ Generate questions test passed!")
                return True
            else:
                print("❌ Generate questions test failed: invalid response structure")
                return False
        else:
            print(f"❌ Generate questions test failed: status code {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Generate questions test failed: {e}")
        return False

def test_get_metadata() -> bool:
    """Test the getMetadata endpoint"""
    print_section("Testing Get Metadata")
    
    payload = {
        "inputs": {
            "url": "https://example.com/article",
            "query": "test query",
            "tag_prompt": "Generate 5 tags"
        },
        "user": "test_user"
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/getMetadata",
            json=payload,
            timeout=TIMEOUT
        )
        print(f"Request payload:")
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        print("\nResponse:")
        print_response(response)
        
        if response.status_code == 200:
            data = response.json()
            if "data" in data and "outputs" in data["data"]:
                print("✅ Get metadata test passed!")
                return True
            else:
                print("❌ Get metadata test failed: invalid response structure")
                return False
        else:
            print(f"❌ Get metadata test failed: status code {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Get metadata test failed: {e}")
        return False

def test_get_answer_non_stream() -> bool:
    """Test the getAnswer endpoint (non-streaming)"""
    print_section("Testing Get Answer (Non-Streaming)")
    
    payload = {
        "inputs": {
            "query": "What is this article about?",
            "url": "https://example.com/article",
            "prompt": "Provide a brief summary",
            "lang": "zh-tw"
        },
        "user": "test_user",
        "stream": False
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/getAnswer",
            json=payload,
            timeout=TIMEOUT
        )
        print(f"Request payload:")
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        print("\nResponse:")
        print_response(response)
        
        if response.status_code == 200:
            data = response.json()
            if "data" in data and "outputs" in data["data"]:
                print("✅ Get answer (non-streaming) test passed!")
                return True
            else:
                print("❌ Get answer test failed: invalid response structure")
                return False
        else:
            print(f"❌ Get answer test failed: status code {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Get answer test failed: {e}")
        return False

def test_get_answer_stream() -> bool:
    """Test the getAnswer endpoint (streaming)"""
    print_section("Testing Get Answer (Streaming)")
    
    payload = {
        "inputs": {
            "query": "What is this article about?",
            "url": "https://example.com/article",
            "lang": "zh-tw"
        },
        "user": "test_user",
        "stream": True
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/getAnswer",
            json=payload,
            stream=True,
            timeout=TIMEOUT
        )
        
        print(f"Request payload:")
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print("\nStreaming events:")
        print("-" * 60)
        
        if response.status_code == 200:
            event_count = 0
            for line in response.iter_lines():
                if line:
                    line_text = line.decode('utf-8')
                    print(line_text)
                    if line_text.startswith("data:"):
                        event_count += 1
                    
                    # Limit output for demo
                    if event_count >= 10:
                        print("... (truncated)")
                        break
            
            print("-" * 60)
            if event_count > 0:
                print(f"✅ Get answer (streaming) test passed! ({event_count} events received)")
                return True
            else:
                print("❌ Get answer (streaming) test failed: no events received")
                return False
        else:
            print(f"❌ Get answer (streaming) test failed: status code {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Get answer (streaming) test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("  AIGC MVP API Server Test Suite")
    print("="*60)
    print(f"\nTesting API server at: {API_BASE_URL}")
    print("Make sure the server is running before starting tests!\n")
    
    # Check if server is reachable
    try:
        requests.get(f"{API_BASE_URL}/health", timeout=2)
    except requests.exceptions.RequestException:
        print(f"❌ ERROR: Cannot connect to server at {API_BASE_URL}")
        print("   Please make sure the server is running:")
        print("   python run.py")
        sys.exit(1)
    
    results = []
    
    # Run tests
    results.append(("Health Check", test_health_check()))
    results.append(("Generate Questions", test_generate_questions()))
    results.append(("Get Metadata", test_get_metadata()))
    results.append(("Get Answer (Non-Streaming)", test_get_answer_non_stream()))
    results.append(("Get Answer (Streaming)", test_get_answer_stream()))
    
    # Print summary
    print_section("Test Summary")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        sys.exit(1)

if __name__ == "__main__":
    main()

