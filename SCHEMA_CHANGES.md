# API Schema Changes Summary

## Overview

Updated the Jira Assistant API to use a simplified, unified response structure.

---

## What Changed

### ❌ Old Schema

**Request:**
```json
{
  "query": "string",
  "conversation_id": "string | null"
}
```

**Response:**
```json
{
  "response": "string",
  "intent": "string | null",
  "similar_tickets": [...],
  "created_ticket": {...} | null,
  "action_type": "string | null",
  "error": "string | null",
  "timestamp": "string"
}
```

### ✅ New Schema

**Request:**
```json
{
  "session_id": "string",
  "question": "string"
}
```

**Response:**
```json
{
  "session_id": "string",
  "message": "string",
  "tickets": [...],
  "type": "SIMILAR" | "CREATED" | "UPDATED",
  "error": "string | null"
}
```

---

## Key Improvements

### 1. **Unified Tickets Field**
- **Before**: Separate `similar_tickets` and `created_ticket` fields
- **After**: Single `tickets` array for all ticket types
- **Benefit**: Simpler to parse and display

### 2. **Clear Type Indicator**
- **Before**: Multiple fields (`intent`, `action_type`, `similar_tickets`, `created_ticket`) to determine what happened
- **After**: Single `type` field with clear values: `SIMILAR`, `CREATED`, or `UPDATED`
- **Benefit**: Easier to handle different response types

### 3. **Cleaner Request**
- **Before**: `query` and optional `conversation_id`
- **After**: `question` and required `session_id`
- **Benefit**: More intuitive naming, enforced session tracking

### 4. **Simplified Response**
- **Before**: 7 fields including redundant ones
- **After**: 5 fields with clear purposes
- **Benefit**: Smaller payloads, easier to validate

---

## Migration Guide

### For API Consumers

#### Request Changes
```javascript
// OLD
const response = await fetch('/chat', {
  method: 'POST',
  body: JSON.stringify({
    query: "find login issues",
    conversation_id: "user-123"
  })
});

// NEW
const response = await fetch('/chat', {
  method: 'POST',
  body: JSON.stringify({
    question: "find login issues",
    session_id: "user-123"
  })
});
```

#### Response Handling
```javascript
// OLD
const data = await response.json();
if (data.similar_tickets.length > 0) {
  // Show similar tickets
  displayTickets(data.similar_tickets);
} else if (data.created_ticket) {
  // Show created ticket
  displayTicket(data.created_ticket);
}

// NEW
const data = await response.json();
switch (data.type) {
  case 'SIMILAR':
    displaySimilarTickets(data.tickets);
    break;
  case 'CREATED':
    displayCreatedTicket(data.tickets[0]);
    break;
  case 'UPDATED':
    displayUpdatedTicket(data.tickets[0]);
    break;
}
```

---

## Files Changed

1. **`src/api/main.py`**
   - Updated `ChatRequest` model
   - Updated `ChatResponse` model
   - Modified `/chat` endpoint logic
   - Modified `/chat/stream` endpoint logic

2. **`streamlit_app.py`**
   - Updated `send_chat_message()` function
   - Updated `send_chat_message_stream()` function
   - Updated message display logic to handle `type` field

3. **`test_stream.py`**
   - Updated to use new request/response format

---

## Type Field Details

| Type | When Used | Tickets Content | Similarity Score |
|------|-----------|-----------------|------------------|
| `SIMILAR` | Similar tickets found | All matching tickets | Present (0.0-1.0) |
| `CREATED` | New ticket created | Single created ticket | `null` |
| `UPDATED` | Ticket updated | Single updated ticket | `null` |

---

## Breaking Changes

⚠️ **This is a breaking change.** Clients using the old schema must update.

### Required Client Updates:

1. **Request Field Names**:
   - `query` → `question`
   - `conversation_id` → `session_id`

2. **Response Field Names**:
   - `response` → `message`
   - `similar_tickets` + `created_ticket` → `tickets`
   - `intent` + `action_type` → `type`

3. **Response Structure**:
   - Check `type` field instead of checking multiple conditionals
   - Access tickets from unified `tickets` array

---

## Testing

Run the test script to verify the new API:

```bash
./test_api.sh
```

Or test manually:

```bash
# Test search
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-123",
    "question": "find tickets about jira testing"
  }'

# Expected response:
# {
#   "session_id": "test-123",
#   "message": "I found 5 similar tickets...",
#   "tickets": [...],
#   "type": "SIMILAR",
#   "error": null
# }
```

---

## Backwards Compatibility

❌ **No backwards compatibility** - this is a breaking change.

If you need to support both versions temporarily:
1. Deploy new API to a different endpoint (`/v2/chat`)
2. Migrate clients gradually
3. Deprecate old endpoint after migration period

---

## Additional Features Implemented

Along with the schema changes, we also added:

1. **Real-time Streaming Events** (`/chat/stream`)
   - Server-Sent Events (SSE) for progress updates
   - Events: start, guardrail, orchestrator, similarity, complete

2. **Fixed Similarity Threshold**
   - Changed from 0.7 → 0.3 for better recall
   - Now finding relevant tickets that were previously filtered out

3. **Improved Logging**
   - Detailed similarity scores in logs
   - Better error messages

---

## Questions?

See `API_SCHEMA.md` for complete API documentation.

