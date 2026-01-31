# Architecture Documentation

## System Overview

The Jira Assistant is a multi-agent system built with LangGraph that provides intelligent Jira ticket management through natural language interactions.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        FastAPI Server                        │
│                     (src/api/main.py)                        │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    LangGraph Workflow                        │
│                  (src/graphs/jira_graph.py)                  │
│                                                              │
│  ┌──────────────┐   ┌────────────────┐   ┌──────────────┐ │
│  │  Guardrail   │──▶│  Orchestrator  │──▶│  Similarity  │ │
│  │    Agent     │   │     Agent      │   │    Agent     │ │
│  └──────────────┘   └────────────────┘   └──────┬───────┘ │
│                                                   │          │
│                           ┌───────────────────────┘          │
│                           ▼                                  │
│                    ┌──────────────┐                         │
│                    │  Jira Agent  │                         │
│                    └──────────────┘                         │
└─────────────────────────────────────────────────────────────┘
                         │           │
         ┌───────────────┘           └───────────────┐
         ▼                                           ▼
┌─────────────────────┐                    ┌──────────────────┐
│   Jira API Service  │                    │   Vector Store   │
│ (src/services/      │                    │     (FAISS)      │
│  jira_service.py)   │                    │ (src/services/   │
└─────────────────────┘                    │  vector_store.py)│
         │                                  └──────────────────┘
         ▼                                           ▲
┌─────────────────────┐                             │
│   Jira Cloud API    │                             │
│ (Atlassian JIRA)    │                    ┌────────┴─────────┐
└─────────────────────┘                    │  Sync Job        │
                                           │ (Background)     │
                                           │ Every 24h        │
                                           └──────────────────┘
```

## Components

### 1. Agents (src/agents/)

#### Guardrail Agent
- **Purpose**: Validate user requests and filter inappropriate content
- **Input**: Raw user query
- **Output**: Validation result (valid/invalid)
- **Technology**: OpenAI GPT-4 with classification prompt

#### Orchestrator Agent
- **Purpose**: Classify user intent and route to appropriate agent
- **Input**: Validated user query
- **Output**: Intent classification (search, create, update, info)
- **Technology**: OpenAI GPT-4 with intent classification prompt

#### Similarity Agent
- **Purpose**: Find existing tickets similar to user query
- **Input**: User query
- **Output**: List of similar tickets with similarity scores
- **Technology**: 
  - LangChain agent with function calling
  - FAISS vector search
  - Sentence-transformers embeddings

#### Jira Agent
- **Purpose**: Create and update Jira tickets
- **Input**: User query + context (similar tickets if any)
- **Output**: Created/updated ticket information
- **Technology**: 
  - LangChain agent with function calling
  - Jira API tools

### 2. Services (src/services/)

#### JiraService
- **Purpose**: Interface with Jira Cloud API
- **Capabilities**:
  - Fetch all tickets from project
  - Create new tickets
  - Update existing tickets
  - Get ticket by key
- **Features**:
  - Automatic retry with exponential backoff
  - Error handling and logging
  - Type conversion (Jira Issue → JiraTicket)

#### VectorStore
- **Purpose**: Manage FAISS vector database
- **Capabilities**:
  - Add ticket embeddings
  - Search for similar tickets
  - Persist/load index from disk
  - Rebuild entire index
- **Implementation**:
  - FAISS IndexFlatL2 (L2 distance)
  - Pickle for metadata storage
  - 384-dimensional vectors

#### EmbeddingsService
- **Purpose**: Generate vector embeddings from text
- **Model**: all-MiniLM-L6-v2 (sentence-transformers)
- **Capabilities**:
  - Single embedding generation
  - Batch embedding generation
  - Ticket-to-text conversion

### 3. Tools (src/tools/)

LangChain tools that agents can invoke:

#### Jira Tools
- `create_jira_ticket_tool`: Create new ticket
- `update_jira_ticket_tool`: Update existing ticket
- `get_jira_ticket_tool`: Retrieve ticket information

#### Vector Search Tools
- `search_similar_tickets_tool`: Search for similar tickets

### 4. Graph Workflow (src/graphs/)

LangGraph state machine that orchestrates agent execution:

```
Entry → Guardrail → Orchestrator → [Similarity|Jira|Final] → End
```

**Decision Points**:

1. **After Guardrail**: 
   - Valid → Continue to Orchestrator
   - Invalid → End (return error message)

2. **After Orchestrator**:
   - Intent = "search" → Similarity Agent
   - Intent = "create" → Similarity Agent (check duplicates first)
   - Intent = "update" → Jira Agent
   - Intent = "info" → Final Response

3. **After Similarity**:
   - Intent = "create" AND no duplicates → Jira Agent
   - Intent = "create" AND duplicates found → Final Response (show similar)
   - Intent = "search" → Final Response (show results)

### 5. Background Jobs (src/jobs/)

#### TicketSyncJob
- **Purpose**: Keep vector store synchronized with Jira
- **Schedule**: 
  - On startup (if configured)
  - Every 24 hours (configurable)
- **Process**:
  1. Fetch all tickets from Jira
  2. Convert tickets to searchable text
  3. Generate embeddings using sentence-transformers
  4. Rebuild FAISS index
  5. Persist to disk
- **Technology**: APScheduler (AsyncIO)

### 6. API (src/api/)

FastAPI REST API with async support:

**Endpoints**:
- `POST /chat`: Main chat interface
- `POST /sync`: Manually trigger sync job
- `GET /stats`: Vector store statistics
- `GET /health`: Health check

**Features**:
- CORS middleware
- Request/response validation with Pydantic
- Async request handling
- Lifespan management (startup/shutdown)

## Data Flow

### Search Flow

```
User: "Find tickets about login issues"
  ↓
Guardrail: ✓ Valid
  ↓
Orchestrator: Intent = "search"
  ↓
Similarity Agent:
  1. Generate embedding for query
  2. Search FAISS index
  3. Return top 5 similar tickets
  ↓
Final Response: Format and return tickets
```

### Create Flow

```
User: "Create a bug for payment timeout"
  ↓
Guardrail: ✓ Valid
  ↓
Orchestrator: Intent = "create"
  ↓
Similarity Agent:
  1. Search for similar tickets
  2. Found 2 tickets with <90% similarity
  ↓
Jira Agent:
  1. Extract ticket details from query
  2. Call create_jira_ticket_tool
  3. Ticket PROJ-456 created
  ↓
Return: Created ticket information
```

### Update Flow

```
User: "Update PROJ-123 priority to High"
  ↓
Guardrail: ✓ Valid
  ↓
Orchestrator: Intent = "update"
  ↓
Jira Agent:
  1. Extract ticket key and updates
  2. Call update_jira_ticket_tool
  3. Ticket updated successfully
  ↓
Return: Updated ticket information
```

## State Management

**AgentState** (TypedDict):
```python
{
    "user_query": str,              # Original query
    "intent": str,                  # Classified intent
    "is_valid_request": bool,       # Guardrail result
    "guardrail_message": str,       # Rejection reason if invalid
    "similar_tickets": List[dict],  # Similar tickets found
    "has_similar_tickets": bool,    # Whether similar found
    "action_type": str,             # create/update/none
    "created_ticket": dict,         # Created/updated ticket
    "final_response": str,          # Response to user
    "error": str,                   # Error if any
    "timestamp": str,               # Request timestamp
    "conversation_id": str          # Conversation ID
}
```

## Vector Search Algorithm

1. **Indexing**:
   - Tickets converted to text: "Summary: ... | Description: ... | Type: ..."
   - Text embedded using all-MiniLM-L6-v2 → 384-dim vectors
   - Vectors added to FAISS IndexFlatL2
   - Metadata stored separately with pickle

2. **Searching**:
   - Query embedded using same model
   - FAISS finds k-nearest neighbors (L2 distance)
   - Distances converted to similarity scores: `1 / (1 + distance)`
   - Results filtered by threshold (default 0.7)
   - Tickets returned with similarity scores

## Configuration

All configuration via environment variables (see `src/config/settings.py`):

- **OpenAI**: Model selection, API key
- **Jira**: URL, credentials, project key
- **Vector Store**: Path, index name
- **Sync Job**: Interval, startup behavior
- **Server**: Host, port, logging
- **Agent**: Similarity threshold, max results

## Scaling Considerations

### Current Architecture (Single Server)
- Suitable for: Small-medium teams (up to 10,000 tickets)
- Bottleneck: In-memory FAISS index

### Scaling Options

1. **More Tickets**: 
   - Switch to FAISS IndexIVFFlat (clustered index)
   - Use GPU-accelerated FAISS

2. **More Users**:
   - Deploy multiple API instances behind load balancer
   - Share vector store via network file system
   - Or use distributed vector DB (Pinecone, Weaviate)

3. **Multiple Projects**:
   - Create separate FAISS indices per project
   - Add project routing in API layer

4. **Real-time Sync**:
   - Replace periodic sync with webhook-based updates
   - Implement incremental index updates

## Security

1. **Guardrail Agent**: Filters malicious/inappropriate requests
2. **Jira Permissions**: Service account should have minimum required permissions
3. **API Security**: Add authentication middleware for production
4. **Secrets**: All credentials via environment variables
5. **Input Validation**: Pydantic models validate all inputs

## Monitoring

### Logs
- Console: Formatted with colors (loguru)
- File: `logs/jira_assistant.log` (rotated, 10-day retention)

### Metrics
- API response times
- Agent execution times
- Vector search performance
- Sync job status

### Health Checks
- `/health` endpoint
- Sync job monitoring
- Vector store size tracking

## Error Handling

1. **Jira API Errors**: Retry with exponential backoff (3 attempts)
2. **OpenAI Errors**: Graceful degradation, log errors
3. **Vector Store Errors**: Initialize empty if corrupted
4. **Agent Errors**: Return user-friendly error messages

## Testing Strategy

1. **Unit Tests**: Test individual services and tools
2. **Integration Tests**: Test API endpoints
3. **Agent Tests**: Test agent decision-making
4. **E2E Tests**: Test complete workflows

---

Built with LangGraph, FastAPI, FAISS, and OpenAI GPT-4

