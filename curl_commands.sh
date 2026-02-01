#!/bin/bash
# =============================================================================
# Manual cURL Commands for Jira Assistant API
# =============================================================================
# Prerequisites: Start the API server first
#   python main.py
#
# Usage: Run individual commands or source this file and run functions
# =============================================================================

API_URL="${API_URL:-http://localhost:8000}"

echo "API Base URL: $API_URL"
echo ""

# -----------------------------------------------------------------------------
# 1. Health & Status
# -----------------------------------------------------------------------------
echo "=== 1. Health Check ==="
curl -s "$API_URL/health" | python3 -m json.tool

echo ""
echo "=== 2. Root Endpoint ==="
curl -s "$API_URL/" | python3 -m json.tool

echo ""
echo "=== 3. Vector Store Stats ==="
curl -s "$API_URL/stats" | python3 -m json.tool

# -----------------------------------------------------------------------------
# 4. Chat - First Turn (Similarity / Check)
# -----------------------------------------------------------------------------
echo ""
echo "=== 4. First Turn: Check similar tickets ==="
curl -s -X POST "$API_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "manual-test-001",
    "question": "Check if there are tickets about login bug"
  }' | python3 -m json.tool

# -----------------------------------------------------------------------------
# 5. Chat - Second Turn (Create - follow-up)
# -----------------------------------------------------------------------------
echo ""
echo "=== 5. Second Turn: Create new ticket (follow-up) ==="
curl -s -X POST "$API_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "manual-test-001",
    "question": "Create a new ticket for this"
  }' | python3 -m json.tool

# -----------------------------------------------------------------------------
# 6. Chat - Direct Create
# -----------------------------------------------------------------------------
echo ""
echo "=== 6. New Session: Direct create request ==="
curl -s -X POST "$API_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "manual-test-002",
    "question": "Create a bug for payment timeout when user checks out"
  }' | python3 -m json.tool

# -----------------------------------------------------------------------------
# 7. Chat - Verify intent
# -----------------------------------------------------------------------------
echo ""
echo "=== 7. Verify similar tickets exist ==="
curl -s -X POST "$API_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "manual-test-003",
    "question": "Verify if similar tickets exist for API timeout issues"
  }' | python3 -m json.tool

# -----------------------------------------------------------------------------
# 8. Chat - Update intent
# -----------------------------------------------------------------------------
echo ""
echo "=== 8. Update existing ticket ==="
curl -s -X POST "$API_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "manual-test-004",
    "question": "Update PROJ-123 priority to High"
  }' | python3 -m json.tool

# -----------------------------------------------------------------------------
# 9. Chat - Empty question (expect 400)
# -----------------------------------------------------------------------------
echo ""
echo "=== 9. Empty question (expect 400) ==="
curl -s -w "\nHTTP Status: %{http_code}\n" -X POST "$API_URL/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "manual-test-005",
    "question": ""
  }'

# -----------------------------------------------------------------------------
# 10. Trigger Sync
# -----------------------------------------------------------------------------
echo ""
echo "=== 10. Trigger Ticket Sync ==="
curl -s -X POST "$API_URL/sync" | python3 -m json.tool
