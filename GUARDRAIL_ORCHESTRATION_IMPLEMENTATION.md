# Guardrail & Orchestration Agent Implementation

## Overview

End-to-end implementation of the Guardrail and Orchestration agents with LangGraph, session management, and intelligent routing between Similarity and Jira agents.

## Architecture Flow

```
User Query
    │
    ▼
┌─────────────────────┐
│  Guardrail Agent    │  ← Uses ChatGPT (gpt-4o-mini)
│  - Validates query  │  ← Stores session_id
│  - Pass/Reject      │
└──────────┬──────────┘
           │ Valid
           ▼
┌─────────────────────┐
│ Orchestration Agent │  ← Keyword + LLM routing
│  - Session check    │
│  - Intent routing   │
└──────────┬──────────┘
           │
     ┌─────┴─────┬──────────────┐
     ▼           ▼              ▼
┌──────────┐ ┌──────────┐ ┌──────────┐
│Similarity│ │  Jira    │ │  Final   │
│  Agent   │ │  Agent   │ │  (Info)  │
└────┬─────┘ └──────────┘ └──────────┘
     │
     ▼
Check historical data → Search → Return to UI
     │
     ▼ (User decides: create/update)
     │
Next turn → Jira Agent
```

## Routing Logic (Orchestrator)

| Condition | Route To | Intent |
|-----------|----------|--------|
| **First turn** in session | Similarity | search |
| Keywords: create, update, add, modify, edit | Jira | create/update |
| Keywords: check, verify, search, find, similar | Similarity | search |
| Ambiguous | LLM decides | - |

### Keyword Lists

- **Jira (create/update)**: create, add, new ticket, update, modify, change, edit, set status, mark as
- **Similarity (check/verify)**: check, verify, search, find, look up, exists, similar, duplicate, match

## Files Created/Modified

### New Files
- `src/services/session_store.py` - In-memory session management

### Modified Files
- `src/agents/guardrail_agent.py` - ChatGPT model, session storage
- `src/agents/orchestrator_agent.py` - Keyword-based routing + LLM fallback
- `src/agents/similarity_agent.py` - Historical data check, session storage
- `src/models/state.py` - New fields: session_exists, is_first_turn, route_to, has_historical_data
- `src/graphs/jira_graph.py` - New routing, final response for user decision
- `src/tools/vector_search_tools.py` - `has_historical_data()` function
- `src/config/settings.py` - `guardrail_model` setting
- `src/api/main.py` - Response type handling
- `src/services/__init__.py` - SessionStore export
- `.env.example` - GUARDRAIL_MODEL
- `streamlit_app.py` - Updated help text

## Configuration

Add to `.env` (optional - has default):
```
GUARDRAIL_MODEL=gpt-4o-mini
```

Options: `gpt-4o-mini`, `gpt-4o`, `gpt-4-turbo`, `gpt-3.5-turbo`

## Session Flow

1. **Turn 1** (First message):
   - Guardrail validates → stores session_id
   - Orchestrator: first turn → Similarity
   - Similarity: checks `has_historical_data()`, searches, returns tickets or empty
   - UI shows results + "Create new ticket?" / "Update [key]?"

2. **Turn 2** (User decides):
   - User: "Create new ticket" or "Update PROJ-123 to Done"
   - Guardrail validates
   - Orchestrator: create/update keywords → Jira
   - Jira agent creates or updates ticket

## API Usage

```bash
# Chat (with session_id for multi-turn)
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "session-123", "question": "Check if there are tickets about login bug"}'
```

Response types: `SIMILAR` | `CREATED` | `UPDATED`

## Running

```bash
# Install dependencies
pip install -r requirements.txt

# Start API
python main.py

# Start UI (separate terminal)
streamlit run streamlit_app.py
```

## Testing Scenarios

1. **First turn → Similarity**: "Check if similar tickets exist for payment timeout"
2. **Second turn → Jira create**: "Create a new ticket for this"
3. **Direct create**: "Create a bug for login issue"
4. **Direct update**: "Update PROJ-123 status to Done"
