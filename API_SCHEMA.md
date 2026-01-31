# Jira Assistant API Schema

## Base URL
```
http://localhost:8000
```

---

## Endpoints

### 1. POST `/chat`

Main chat endpoint for synchronous responses.

#### Request Body

```json
{
  "session_id": "string",
  "question": "string"
}
```

**Fields:**
- `session_id` (required): Unique identifier for the user session
- `question` (required): User's question or request about Jira tickets

**Example:**
```json
{
  "session_id": "user-123-session",
  "question": "find tickets about login issues"
}
```

#### Response Body

```json
{
  "session_id": "string",
  "message": "string",
  "tickets": [
    {
      "key": "string",
      "summary": "string",
      "description": "string",
      "status": "string",
      "priority": "string",
      "similarity_score": "float | null"
    }
  ],
  "type": "string",
  "error": "string | null"
}
```

**Fields:**
- `session_id`: Echo of the request session_id
- `message`: AI assistant's response message
- `tickets`: List of ticket objects (can be similar, created, or updated tickets)
- `type`: Operation type - one of:
  - `"SIMILAR"` - Similar tickets were found
  - `"CREATED"` - New ticket was created
  - `"UPDATED"` - Existing ticket was updated
- `error`: Error message if operation failed, otherwise `null`

**Example Response (SIMILAR):**
```json
{
  "session_id": "user-123-session",
  "message": "I found 3 similar tickets related to login issues.",
  "tickets": [
    {
      "key": "SCRUM-5",
      "summary": "Login button not working",
      "description": "Users cannot click the login button",
      "status": "To Do",
      "priority": "High",
      "similarity_score": 0.89
    },
    {
      "key": "SCRUM-12",
      "summary": "Authentication timeout",
      "description": "Login times out after 30 seconds",
      "status": "In Progress",
      "priority": "Medium",
      "similarity_score": 0.76
    }
  ],
  "type": "SIMILAR",
  "error": null
}
```

**Example Response (CREATED):**
```json
{
  "session_id": "user-123-session",
  "message": "Created new ticket SCRUM-25 for the payment timeout issue.",
  "tickets": [
    {
      "key": "SCRUM-25",
      "summary": "Payment timeout after checkout",
      "description": "Users experience timeout when completing payment",
      "status": "To Do",
      "priority": "High",
      "similarity_score": null
    }
  ],
  "type": "CREATED",
  "error": null
}
```

**Example Response (UPDATED):**
```json
{
  "session_id": "user-123-session",
  "message": "Updated ticket SCRUM-5 priority to High.",
  "tickets": [
    {
      "key": "SCRUM-5",
      "summary": "Login button not working",
      "description": "Users cannot click the login button",
      "status": "In Progress",
      "priority": "High",
      "similarity_score": null
    }
  ],
  "type": "UPDATED",
  "error": null
}
```

**Example Response (ERROR):**
```json
{
  "session_id": "user-123-session",
  "message": "",
  "tickets": [],
  "type": "SIMILAR",
  "error": "Failed to connect to Jira API"
}
```

---

### 2. POST `/chat/stream`

Streaming endpoint that sends real-time Server-Sent Events (SSE).

#### Request Body

Same as `/chat`:
```json
{
  "session_id": "string",
  "question": "string"
}
```

#### Response Format

Content-Type: `text/event-stream`

The response is a stream of Server-Sent Events. Each event has the format:
```
data: {"event": "event_type", "message": "...", "timestamp": "..."}

```

**Event Types:**

1. **start** - Processing began
   ```json
   {"event": "start", "message": "Processing your request...", "timestamp": "2026-01-31T..."}
   ```

2. **guardrail** - Validating request
   ```json
   {"event": "guardrail", "message": "🛡️  Validating request...", "timestamp": "2026-01-31T..."}
   ```

3. **orchestrator** - Analyzing intent
   ```json
   {"event": "orchestrator", "message": "🧠 Analyzing intent...", "timestamp": "2026-01-31T..."}
   ```

4. **similarity** - Searching for tickets
   ```json
   {"event": "similarity", "message": "🔍 Searching for similar tickets...", "timestamp": "2026-01-31T..."}
   ```

5. **similarity_found** - Similar tickets found
   ```json
   {"event": "similarity_found", "message": "✅ Found 5 similar tickets!", "count": 5, "timestamp": "2026-01-31T..."}
   ```

6. **similarity_not_found** - No similar tickets
   ```json
   {"event": "similarity_not_found", "message": "📝 No similar tickets found", "timestamp": "2026-01-31T..."}
   ```

7. **ticket_created** - Ticket was created (intent: create)
   ```json
   {"event": "ticket_created", "message": "🎉 Created ticket SCRUM-25!", "ticket_key": "SCRUM-25", "timestamp": "2026-01-31T..."}
   ```

8. **ticket_updated** - Ticket was updated (intent: update)
   ```json
   {"event": "ticket_updated", "message": "✨ Updated ticket SCRUM-5!", "ticket_key": "SCRUM-5", "timestamp": "2026-01-31T..."}
   ```

9. **complete** - Final result
   ```json
   {
     "event": "complete",
     "result": {
       "session_id": "user-123-session",
       "message": "...",
       "tickets": [...],
       "type": "SIMILAR",
       "error": null
     },
     "timestamp": "2026-01-31T..."
   }
   ```

10. **error** - Error occurred
   ```json
   {"event": "error", "message": "Error message...", "timestamp": "2026-01-31T..."}
   ```

---

### 3. GET `/health`

Health check endpoint.

#### Response
```json
{
  "status": "healthy",
  "service": "jira-assistant"
}
```

---

### 4. GET `/stats`

Get vector store statistics.

#### Response
```json
{
  "total_tickets": 42,
  "dimension": 384,
  "index_path": "/path/to/vector/store"
}
```

---

### 5. POST `/sync`

Manually trigger ticket synchronization.

#### Response
```json
{
  "message": "Ticket sync triggered successfully",
  "status": "running"
}
```

---

## Workflow & Type Determination

The system uses a multi-agent architecture to determine the `type`:

```
User Question
    ↓
Guardrail Agent (validates request)
    ↓
Orchestrator Agent (classifies intent: search/create/update)
    ↓
    ├─ Intent: "search" → Similarity Agent
    │                      ↓
    │                   Find similar tickets
    │                      ↓
    │                   type = SIMILAR
    │
    ├─ Intent: "create" → Jira Agent
    │                      ↓
    │                   Create new ticket
    │                      ↓
    │                   type = CREATED
    │
    └─ Intent: "update" → Jira Agent
                           ↓
                       Update existing ticket
                           ↓
                       type = UPDATED
```

**Key Points:**
- The `intent` field from the orchestrator directly determines the `type`
- `SIMILAR` → Only similarity agent was called (search operation)
- `CREATED` → Jira agent was invoked to create a ticket
- `UPDATED` → Jira agent was invoked to update a ticket

---

## Ticket Object Schema

```typescript
{
  key: string           // Jira ticket key (e.g., "SCRUM-5")
  summary: string       // Ticket title
  description: string   // Ticket description
  status: string        // Current status (e.g., "To Do", "In Progress", "Done")
  priority: string      // Priority level (e.g., "High", "Medium", "Low", "None")
  similarity_score?: number  // Similarity score (0.0-1.0) for SIMILAR type, null for CREATED/UPDATED
}
```

---

## Type Field Values

The `type` field indicates which agent was invoked and what action was taken:

| Type | When Set | What Happened | Tickets Content |
|------|----------|---------------|-----------------|
| `SIMILAR` | Similarity agent called | Similar tickets were found and returned to user | All matching tickets with similarity scores |
| `CREATED` | Jira agent called to create | New ticket was created in Jira | Single newly created ticket (no similarity score) |
| `UPDATED` | Jira agent called to update | Existing ticket was updated in Jira | Single updated ticket (no similarity score) |

**Logic:**
- If user searches for tickets → Similarity agent runs → `type = SIMILAR`
- If user requests ticket creation → Jira agent creates ticket → `type = CREATED`
- If user requests ticket update → Jira agent updates ticket → `type = UPDATED`

---

## Error Handling

When an error occurs:
- `error` field contains the error message
- `message` field is empty or contains partial response
- `tickets` array is empty
- `type` defaults to `"SIMILAR"`

**Example:**
```json
{
  "session_id": "user-123-session",
  "message": "",
  "tickets": [],
  "type": "SIMILAR",
  "error": "Connection timeout to Jira API"
}
```

---

## Configuration

Default server configuration:
- **Host**: `0.0.0.0`
- **Port**: `8000`
- **Similarity Threshold**: `0.3` (configurable via `SIMILARITY_THRESHOLD` in `.env`)

---

## Example Usage

### Python (requests)

```python
import requests

# Synchronous request
response = requests.post(
    "http://localhost:8000/chat",
    json={
        "session_id": "my-session",
        "question": "find bugs related to authentication"
    }
)
result = response.json()
print(f"Type: {result['type']}")
print(f"Message: {result['message']}")
print(f"Tickets: {len(result['tickets'])}")
```

### cURL

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-123",
    "question": "find tickets about login issues"
  }'
```

### JavaScript (fetch)

```javascript
const response = await fetch('http://localhost:8000/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    session_id: 'browser-session-456',
    question: 'create a bug for payment timeout'
  })
});

const result = await response.json();
console.log(`Type: ${result.type}`);
console.log(`Tickets:`, result.tickets);
```

### Streaming (JavaScript EventSource)

```javascript
const eventSource = new EventSource(
  'http://localhost:8000/chat/stream?' + 
  new URLSearchParams({
    session_id: 'stream-session',
    question: 'find all high priority bugs'
  })
);

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(`Event: ${data.event}, Message: ${data.message}`);
  
  if (data.event === 'complete') {
    console.log('Final result:', data.result);
    eventSource.close();
  }
};
```

---

## Notes

1. **Session Management**: The `session_id` is used to maintain conversation context across multiple requests
2. **Streaming**: Use `/chat/stream` for real-time progress updates in UI
3. **Similarity Scores**: Only present in SIMILAR type responses, range from 0.0 (no match) to 1.0 (perfect match)
4. **Empty Tickets Array**: Possible when no similar tickets found and no action taken

