#!/bin/bash
# Test script for Jira Assistant API

API_URL="http://localhost:8000"

echo "==============================================="
echo "🧪 Testing Jira Assistant API"
echo "==============================================="
echo ""

# Test 1: Health Check
echo "1️⃣  Testing Health Check..."
echo "   GET $API_URL/health"
curl -s "$API_URL/health" | python3 -m json.tool
echo ""
echo ""

# Test 2: Get Stats
echo "2️⃣  Testing Stats Endpoint..."
echo "   GET $API_URL/stats"
curl -s "$API_URL/stats" | python3 -m json.tool
echo ""
echo ""

# Test 3: Search for Similar Tickets
echo "3️⃣  Testing Search (SIMILAR type expected)..."
echo "   POST $API_URL/chat"
echo '   Body: {"session_id": "test-123", "question": "find tickets about jira testing"}'
curl -s -X POST "$API_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-search-123",
    "question": "find tickets about jira testing"
  }' | python3 -m json.tool
echo ""
echo ""

# Test 4: Create Ticket Request
echo "4️⃣  Testing Create Ticket (CREATED type expected)..."
echo "   POST $API_URL/chat"
echo '   Body: {"session_id": "test-456", "question": "create a bug for slow page load"}'
curl -s -X POST "$API_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-create-456",
    "question": "create a bug for slow page load"
  }' | python3 -m json.tool
echo ""
echo ""

echo "==============================================="
echo "✅ API Tests Complete"
echo "==============================================="

