# Jira Assistant - Multi-Agent Chatbot

A production-grade GenAI multi-agent chatbot for Jira assistance using LangGraph and FAISS vector search.

## 🚀 Features

- **Multi-Agent Architecture**: Orchestrator, Guardrail, Similarity, and Jira agents working together
- **Semantic Search**: FAISS-based vector search for finding similar tickets
- **Intelligent Routing**: Automatically classifies user intent and routes to appropriate agent
- **Guardrails**: Validates requests to prevent misuse
- **Auto-sync**: Periodically syncs Jira tickets and updates vector store
- **RESTful API**: FastAPI-based web service with async support

## 🏗️ Architecture

```
User Query → Guardrail Agent → Orchestrator Agent
                                      ↓
                    ┌─────────────────┼─────────────────┐
                    ↓                 ↓                 ↓
            Similarity Agent    Jira Agent    Final Response
                    ↓                 ↓
              Vector Search    Create/Update Ticket
```

### Agents

1. **Guardrail Agent**: Validates user requests and filters inappropriate content
2. **Orchestrator Agent**: Classifies intent (search, create, update, info)
3. **Similarity Agent**: Searches for similar tickets using FAISS vector store
4. **Jira Agent**: Creates and updates Jira tickets using Jira API

### Background Jobs

- **Ticket Sync Job**: Runs on startup and every 24 hours (configurable)
  - Fetches all Jira tickets
  - Generates embeddings using sentence-transformers
  - Rebuilds FAISS vector store

## 📦 Installation

### Prerequisites

- Python 3.9+
- Jira account with API token
- OpenAI API key

### Setup

1. **Clone and navigate to project**:
```bash
cd jira-hackathon
```

2. **Create virtual environment**:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Configure environment**:
```bash
cp .env.example .env
# Edit .env with your credentials
```

5. **Required environment variables**:
```env
OPENAI_API_KEY=your_openai_api_key
JIRA_URL=https://your-domain.atlassian.net
JIRA_EMAIL=your-email@example.com
JIRA_API_TOKEN=your_jira_api_token
JIRA_PROJECT_KEY=PROJ
```

📚 **See [ENV_SETUP_GUIDE.md](ENV_SETUP_GUIDE.md) for detailed setup instructions**

6. **Validate configuration**:
```bash
python validate_env.py
```

This ensures all secrets are properly configured before starting.

## 🚀 Usage

### Start the Server

```bash
python main.py
```

The API will be available at `http://localhost:8000`

### API Endpoints

#### 1. Chat with Assistant

```bash
POST /chat
Content-Type: application/json

{
  "query": "Find tickets about login issues",
  "conversation_id": "optional-conversation-id"
}
```

**Response**:
```json
{
  "response": "I found 3 similar tickets...",
  "intent": "search",
  "similar_tickets": [
    {
      "key": "PROJ-123",
      "summary": "Login timeout issue",
      "description": "Users experiencing...",
      "status": "In Progress",
      "priority": "High",
      "similarity_score": 0.89
    }
  ],
  "created_ticket": null,
  "action_type": null,
  "timestamp": "2026-01-31T10:00:00"
}
```

#### 2. Manual Sync

```bash
POST /sync
```

Manually trigger a ticket sync job.

#### 3. Statistics

```bash
GET /stats
```

Get vector store statistics.

#### 4. Health Check

```bash
GET /health
```

Check service health.

## 📝 Example Queries

### Search for Tickets
```
"Find tickets about API performance"
"Are there any bugs related to payment processing?"
"Show me tickets about authentication"
```

### Create Tickets
```
"Create a ticket for fixing the login timeout issue"
"I need to report a bug in the payment system"
"Create a task to implement dark mode"
```

### Update Tickets
```
"Update ticket PROJ-123 status to In Progress"
"Change priority of PROJ-456 to High"
```

## 🔧 Configuration

All configuration is in `src/config/settings.py` and can be overridden via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_MODEL` | `gpt-4-turbo-preview` | OpenAI model to use |
| `EMBEDDING_MODEL` | `text-embedding-3-small` | Embedding model |
| `SYNC_INTERVAL_HOURS` | `24` | Hours between syncs |
| `SYNC_ON_STARTUP` | `true` | Run sync on startup |
| `MAX_SIMILARITY_RESULTS` | `5` | Max similar tickets to return |
| `SIMILARITY_THRESHOLD` | `0.7` | Minimum similarity score |
| `PORT` | `8000` | API server port |
| `LOG_LEVEL` | `INFO` | Logging level |

## 📁 Project Structure

```
jira-hackathon/
├── src/
│   ├── agents/              # LangGraph agent nodes
│   │   ├── orchestrator_agent.py
│   │   ├── guardrail_agent.py
│   │   ├── similarity_agent.py
│   │   └── jira_agent.py
│   ├── tools/               # LangChain tools
│   │   ├── jira_tools.py
│   │   └── vector_search_tools.py
│   ├── services/            # Business logic
│   │   ├── jira_service.py
│   │   ├── vector_store.py
│   │   └── embeddings_service.py
│   ├── graphs/              # LangGraph workflows
│   │   └── jira_graph.py
│   ├── jobs/                # Background jobs
│   │   └── sync_tickets.py
│   ├── api/                 # FastAPI endpoints
│   │   └── main.py
│   ├── models/              # Data models
│   │   └── state.py
│   └── config/              # Configuration
│       └── settings.py
├── data/
│   └── vector_store/        # FAISS index storage
├── logs/                    # Application logs
├── main.py                  # Entry point
├── requirements.txt
└── README.md
```

## 🔐 Security

- **Guardrail Agent**: Validates all user requests before processing
- **API Authentication**: Add your own auth middleware in production
- **Environment Variables**: Never commit `.env` file
- **Jira Permissions**: Service account should have minimum required permissions

## 🧪 Testing

```bash
# Install dev dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest tests/
```

## 📊 Monitoring

Logs are written to:
- Console (formatted with colors)
- `logs/jira_assistant.log` (rotated at 500MB, retained for 10 days)

## 🔄 Workflow Logic

1. **User sends query** → Guardrail validates
2. **Orchestrator classifies intent**:
   - `search` → Similarity agent searches vector store
   - `create` → Similarity agent checks for duplicates, then Jira agent creates ticket
   - `update` → Jira agent updates ticket directly
   - `info` → Returns help information

3. **Similarity search** (for search/create):
   - Generates embedding for query
   - Searches FAISS index
   - Returns top-k similar tickets above threshold

4. **Ticket creation**:
   - If >90% similar ticket found, show it instead of creating
   - Otherwise, Jira agent creates new ticket

## 🚀 Production Deployment

### Docker (Recommended)

```bash
# Build image
docker build -t jira-assistant .

# Run container
docker run -d \
  --env-file .env \
  -p 8000:8000 \
  -v ./data:/app/data \
  jira-assistant
```

### Environment Checklist

- [ ] Set all required environment variables
- [ ] Configure Jira API token with proper permissions
- [ ] Set up log rotation and monitoring
- [ ] Add authentication middleware
- [ ] Configure CORS for your domain
- [ ] Set up health check monitoring
- [ ] Configure backup for vector store

## 🤝 Contributing

1. Create feature branch
2. Make changes with tests
3. Run linting: `black src/ && ruff check src/`
4. Submit pull request

## 📄 License

MIT License - see LICENSE file for details

## 📞 Support

For issues and questions:
- Check logs in `logs/jira_assistant.log`
- Review configuration in `.env`
- Test Jira connectivity: `/health` endpoint

## 🎯 Roadmap

- [ ] Add conversation memory for multi-turn dialogs
- [ ] Implement user authentication
- [ ] Add support for attachments
- [ ] Integrate with Slack/Teams
- [ ] Add analytics dashboard
- [ ] Support multiple Jira projects
- [ ] Add ticket assignment capabilities
- [ ] Implement advanced filters for search

---

Built with ❤️ using LangGraph, FastAPI, and FAISS

