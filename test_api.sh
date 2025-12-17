#!/bin/bash
# Sample API test script

API_URL="http://localhost:8000"
API_KEY="dev-local-test-key-please-change"

echo "🧪 Testing Agent Will Smith API"
echo "==========================================="
echo ""

# Test 1: Health Check
echo "1️⃣  Testing /health endpoint..."
curl -s "${API_URL}/health" | jq '.'
echo ""

# Test 2: Readiness Check
echo "2️⃣  Testing /ready endpoint..."
curl -s "${API_URL}/ready" | jq '.'
echo ""

# Test 3: Metrics
echo "3️⃣  Testing /metrics endpoint..."
curl -s "${API_URL}/metrics" | jq '.'
echo ""

# Test 4: Product Recommendations (with auth)
echo "4️⃣  Testing /api/v1/recommend-products endpoint..."
curl -s -X POST "${API_URL}/api/v1/recommend-products" \
  -H "Authorization: Bearer ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "article": "This article explores sustainable living practices, including eco-friendly products, green technologies, and lifestyle changes that help reduce carbon footprint. It covers topics like renewable energy, waste reduction, and conscious consumption patterns for modern families seeking to live more sustainably.",
    "question": "What activities or books would help someone learn more about sustainable living and environmental conservation?",
    "k": 5
  }' | jq '.'
echo ""

# Test 5: Invalid API Key (should fail)
echo "5️⃣  Testing with invalid API key (should return 401)..."
curl -s -X POST "${API_URL}/api/v1/recommend-products" \
  -H "Authorization: Bearer invalid-key" \
  -H "Content-Type: application/json" \
  -d '{
    "article": "Test article",
    "question": "Test question?",
    "k": 1
  }' | jq '.'
echo ""

echo "✅ API tests completed!"

