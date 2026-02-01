# Jira Assistant - Testing Guide

## Overview

This document describes how testing is performed for the Jira Assistant (Guardrail + Orchestration) system.

---

## 1. Manual Testing with cURL

### Prerequisites

1. Start the API server:
   ```bash
   python main.py
   ```
2. Ensure `.env` is configured with valid `OPENAI_API_KEY` and Jira credentials.

### Running cURL Commands

**Option A: Run the curl script (executes all commands)**
```bash
chmod +x curl_commands.sh
./curl_commands.sh
```

**Option B: Run individual commands** (copy from `curl_commands.sh`)

**Health check:**
```bash
curl -s http://localhost:8000/health | python3 -m json.tool
```

**Chat - First turn (check similar tickets):**
```bash
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "manual-001", "question": "Check if there are tickets about login bug"}' \
  | python3 -m json.tool
```

**Chat - Second turn (create follow-up):**
```bash
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "manual-001", "question": "Create a new ticket for this"}' \
  | python3 -m json.tool
```

**Chat - Direct create:**
```bash
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "manual-002", "question": "Create a bug for payment timeout"}' \
  | python3 -m json.tool
```

**Chat - Update ticket:**
```bash
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "manual-003", "question": "Update PROJ-123 priority to High"}' \
  | python3 -m json.tool
```

**Custom base URL:**
```bash
API_URL=http://localhost:8000 ./curl_commands.sh
```

### Quick Copy-Paste cURL Commands

```bash
# Health
curl -s http://localhost:8000/health

# Stats
curl -s http://localhost:8000/stats

# Chat - Check similar
curl -s -X POST http://localhost:8000/chat -H "Content-Type: application/json" -d '{"session_id":"s1","question":"Check if there are tickets about login bug"}'

# Chat - Create follow-up (same session)
curl -s -X POST http://localhost:8000/chat -H "Content-Type: application/json" -d '{"session_id":"s1","question":"Create a new ticket for this"}'

# Chat - Direct create
curl -s -X POST http://localhost:8000/chat -H "Content-Type: application/json" -d '{"session_id":"s2","question":"Create a bug for payment timeout"}'

# Sync
curl -s -X POST http://localhost:8000/sync
```

---

## 2. Integration Tests (Python)

### Guardrail & Orchestration Flow

```bash
# Use .env credentials (ensure OPENAI_API_KEY is not overridden in shell)
unset OPENAI_API_KEY
python3 test_guardrail_orchestration.py
```

**What it tests:**
- First turn → Similarity agent (search intent)
- Second turn "Create a new ticket" → Jira agent (create intent)
- New session with create keywords → Similarity first (by design)
- Verify keywords → Similarity
- Session store persistence across turns

### API Unit Tests (pytest)

```bash
python3 -m pytest tests/test_api.py -v
```

**What it tests:**
- Root endpoint (`/`)
- Health endpoint (`/health`)
- Stats endpoint (`/stats`)
- Chat empty question validation (400)

---

## 3. Test Cases Reference

Test cases are stored in `test_cases.json`. Each case includes:

| Field | Description |
|-------|-------------|
| `id` | Test case ID (TC-001, etc.) |
| `name` | Short description |
| `method` | HTTP method |
| `endpoint` | API path |
| `payload` | Request body (for POST) |
| `expected_status` | Expected HTTP status |
| `expected_intent` | Expected `intent` in response (search/create/update) |
| `expected_type` | Expected `type` in response (SIMILAR/CREATED/UPDATED) |
| `description` | Flow/routing explanation |

---

## 4. Flow & Routing Logic Tested

```
User Query
    ↓
Guardrail (validates, stores session_id)
    ↓ (valid)
Orchestrator (routes based on keywords + session)
    ↓
┌─────────────┬─────────────┬─────────────┐
│ Similarity  │    Jira     │    Final    │
│ (search/    │ (create/    │   (info)    │
│  verify)    │  update)    │             │
└─────────────┴─────────────┴─────────────┘
```

**Routing rules:**
1. **First turn** → Always Similarity (check historical data)
2. **Create/update keywords** (create, update, add, modify, edit) → Jira
3. **Check/verify keywords** (check, verify, search, find, similar) → Similarity

---

## 5. Expected Response Structure

**Chat response (`/chat`):**
```json
{
  "session_id": "string",
  "message": "string",
  "tickets": [
    {
      "key": "PROJ-123",
      "summary": "string",
      "description": "string",
      "status": "string",
      "priority": "string",
      "similarity_score": 0.85
    }
  ],
  "type": "SIMILAR | CREATED | UPDATED",
  "error": null
}
```

---

## 6. Troubleshooting

| Issue | Check |
|-------|-------|
| 401 from OpenAI | Valid `OPENAI_API_KEY` in `.env`, no override in shell |
| No similar tickets | Run sync: `curl -X POST http://localhost:8000/sync` |
| Guardrail blocks valid request | Review `src/agents/guardrail_agent.py` prompt |
| Wrong routing | Check `src/agents/orchestrator_agent.py` keyword lists |

---

## 7. Automated Test Case Runner

Run all test cases from `test_cases.json` against the API:

```bash
# Ensure API is running: python main.py
python3 run_test_cases.py

# Or with custom URL
python3 run_test_cases.py http://localhost:8000
```

---

## 8. Files Reference

| File | Purpose |
|------|---------|
| `curl_commands.sh` | Manual cURL commands for all endpoints |
| `test_cases.json` | Structured test case definitions |
| `run_test_cases.py` | Runs test_cases.json against live API |
| `test_guardrail_orchestration.py` | Integration tests (flow + routing) |
| `tests/test_api.py` | pytest API unit tests |
| `test_api_keys.py` | Validates OpenAI API key from `.env` |
