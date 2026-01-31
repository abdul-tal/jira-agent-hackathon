# Quick Start Guide - OpenAI Embeddings

## Prerequisites

✅ Python 3.9+
✅ OpenAI API key
✅ Jira API access

---

## Step 1: Install Dependencies

```bash
cd jira-hackathon

# Install/upgrade dependencies
pip install -r requirements.txt
```

**Key packages:**
- `langchain==0.3.13` - Text splitting framework
- `langchain-openai==0.2.14` - OpenAI embeddings integration
- `faiss-cpu==1.13.2` - Vector store

---

## Step 2: Configure Environment

Create `.env` file in project root:

```bash
# Required
OPENAI_API_KEY=sk-proj-your-actual-key-here
JIRA_URL=https://your-company.atlassian.net
JIRA_EMAIL=your-email@company.com
JIRA_API_TOKEN=your-jira-api-token
JIRA_PROJECT_KEY=PROJ

# Optional (defaults shown)
SYNC_INTERVAL_HOURS=24
SYNC_ON_STARTUP=true
SIMILARITY_THRESHOLD=0.5
MAX_SIMILARITY_RESULTS=5
```

**Get API keys:**
- OpenAI: https://platform.openai.com/api-keys
- Jira: https://id.atlassian.com/manage-profile/security/api-tokens

---

## Step 3: Clear Old Vector Store (IMPORTANT!)

If you previously used sentence-transformers:

```bash
# Delete old 384-dimension index
rm -rf data/vector_store/*
```

The new OpenAI embeddings are **1536 dimensions** (vs 384), so old index won't work.

---

## Step 4: Start the API

```bash
# Start FastAPI server
python -m uvicorn src.api.main:app --reload --port 8000
```

**What happens on startup:**
1. ✅ Loads settings from `.env`
2. ✅ Initializes OpenAI embeddings service
3. ✅ Fetches all Jira tickets
4. ✅ Converts each ticket to searchable text (no chunking)
5. ✅ Generates OpenAI embeddings (one per ticket)
6. ✅ Builds FAISS index (1536-dim vectors)
7. ✅ Schedules periodic sync (every 24h)

**Expected logs:**
```
[INFO] Embeddings service initialized with OpenAI text-embedding-3-small 
       (dim=1536, no chunking - tickets are small enough)
[INFO] Starting ticket sync job...
[INFO] Fetched 450 tickets from Jira
[INFO] Converting tickets to searchable text...
[INFO] Generating OpenAI embeddings for 450 tickets...
[INFO] Successfully generated 450 embeddings
[INFO] Rebuilt vector store with 450 tickets
[INFO] ✅ Ticket sync completed successfully!
```

---

## Step 5: Test the API

### Health Check

```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "vector_store_size": 1245
}
```

### Search Similar Tickets

```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "login authentication error", "max_results": 5}'
```

**Response:**
```json
{
  "success": true,
  "similar_tickets": [
    {
      "key": "PROJ-123",
      "summary": "LDAP login fails after upgrade",
      "similarity_score": 0.87,
      "status": "In Progress",
      "priority": "High"
    },
    ...
  ],
  "count": 5
}
```

### Trigger Manual Sync

```bash
curl -X POST http://localhost:8000/sync
```

---

## Step 6: Start Streamlit UI (Optional)

```bash
# In a new terminal
streamlit run streamlit_app.py
```

Open browser: http://localhost:8501

---

## Verify Everything Works

### 1. Check Vector Store

```bash
ls -lh data/vector_store/
```

**Expected files:**
- `jira_tickets.index` - FAISS index (1536-dim vectors)
- `jira_tickets_metadata.pkl` - Chunk metadata

### 2. Test Search Quality

Try these queries in the UI or API:

- "authentication fails" → Should find login/auth tickets
- "slow performance" → Should find performance/timeout tickets
- "payment error" → Should find billing/checkout tickets

### 3. Monitor OpenAI Usage

Check usage dashboard:
- https://platform.openai.com/usage

**Expected costs:**
- Initial sync (1000 tickets): $0.01-0.05
- Each query: $0.00002

---

## Common Issues

### Issue: "OPENAI_API_KEY not found"

**Solution:**
```bash
# Check .env file exists
cat .env | grep OPENAI_API_KEY

# Should output: OPENAI_API_KEY=sk-proj-...
```

### Issue: "Dimension mismatch" or "Index is empty"

**Solution:**
```bash
# Delete old vector store
rm -rf data/vector_store/*

# Restart API (will rebuild)
python -m uvicorn src.api.main:app --reload
```

### Issue: "Module 'langchain' not found"

**Solution:**
```bash
pip install --upgrade -r requirements.txt
```

### Issue: Search results are poor

**Solutions:**
1. Lower similarity threshold: `SIMILARITY_THRESHOLD=0.3`
2. Increase results: `MAX_SIMILARITY_RESULTS=10`
3. Wait for full sync to complete
4. Check OpenAI API key is valid

---

## What's Different from Before?

| Feature | Old (Sentence Transformers) | New (OpenAI) |
|---------|------------------------------|--------------|
| Embedding Model | all-MiniLM-L6-v2 (local) | text-embedding-3-small (API) |
| Dimensions | 384 | 1536 |
| Quality | Good | Excellent |
| Cost | Free | ~$0.01 per 1000 tickets |
| Speed | Fast (local) | Slower (API calls) |
| Privacy | Full privacy | Data sent to OpenAI |
| Chunking | None | None (tickets too small to need it) |

---

## Configuration Options

### Use Larger Embedding Model (Optional)

Edit `src/services/embeddings_service.py`:

```python
self.embeddings = OpenAIEmbeddings(
    model="text-embedding-3-large",  # Instead of small
    openai_api_key=settings.openai_api_key
)
self.embedding_dimension = 3072  # Instead of 1536
```

Edit `src/services/vector_store.py`:

```python
def __init__(self, dimension: int = 3072):  # Instead of 1536
```

**Cost:** ~2x more expensive, marginally better quality

---

## Next Steps

1. ✅ Test search with real queries
2. ✅ Adjust `SIMILARITY_THRESHOLD` if needed
3. ✅ Monitor OpenAI usage/costs
4. ✅ Set up production deployment
5. ✅ Configure periodic sync schedule

---

## Documentation

- **Migration Guide:** `MIGRATION_TO_OPENAI.md`
- **Why No Chunking:** `NO_CHUNKING_EXPLANATION.md`
- **API Schema:** `API_SCHEMA.md`
- **Changelog:** `CHANGELOG_OPENAI.md`

---

## Support

- OpenAI Docs: https://platform.openai.com/docs/guides/embeddings
- LangChain Docs: https://python.langchain.com/docs/modules/data_connection/
- FAISS Wiki: https://github.com/facebookresearch/faiss/wiki

---

## Summary

You now have:
- ✅ OpenAI embeddings (1536-dim, high quality)
- ✅ Simple 1:1 mapping (1 ticket = 1 embedding)
- ✅ Improved search quality
- ✅ Automatic sync every 24h
- ✅ Lower cost (no chunking overhead)
- ✅ Faster search (fewer vectors)

**Estimated setup time:** 5 minutes
**Initial sync time:** 1-3 minutes (depending on ticket count)
**Cost:** < $0.05 for initial setup, < $5/year ongoing

