# Quick Start Guide

Get up and running with Jira Assistant in 5 minutes!

## Prerequisites

- Python 3.9 or higher
- Jira account with API access
- OpenAI API key

## Step 1: Get Your Credentials

### Jira API Token

1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Click "Create API token"
3. Give it a name (e.g., "Jira Assistant")
4. Copy the token (save it securely!)

### OpenAI API Key

1. Go to https://platform.openai.com/api-keys
2. Click "Create new secret key"
3. Copy the key (save it securely!)

## Step 2: Install

```bash
# Navigate to project
cd jira-hackathon

# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Step 3: Configure

Create and configure your `.env` file:

```bash
# Copy example
cp .env.example .env

# Edit with your favorite editor
nano .env  # or vim, code, etc.
```

Fill in your credentials:

```env
# OpenAI
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxx

# Jira
JIRA_URL=https://your-company.atlassian.net
JIRA_EMAIL=your.email@company.com
JIRA_API_TOKEN=your_jira_token_here
JIRA_PROJECT_KEY=PROJ  # Your Jira project key
```

**Need help getting credentials?** See [ENV_SETUP_GUIDE.md](ENV_SETUP_GUIDE.md) for detailed instructions.

**Validate your configuration:**

```bash
python validate_env.py
```

This will check that all required secrets are properly configured before you start the server.

## Step 4: Run

```bash
python main.py
```

You'll see:
```
Starting Jira Assistant...
Running initial ticket sync on startup...
Fetched 127 tickets from Jira
Generated 127 embeddings
Ticket sync completed successfully!
```

## Step 5: Test

Open a new terminal and test the API:

### Search for tickets
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "Find tickets about login issues"}'
```

### Create a ticket
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "Create a bug ticket for payment processing timeout"}'
```

### Check stats
```bash
curl http://localhost:8000/stats
```

## Common Issues

### Issue: "No module named 'src'"

**Solution**: Make sure you're in the `jira-hackathon/` directory

### Issue: "Jira authentication failed"

**Solutions**:
- Verify `JIRA_URL` doesn't have trailing slash
- Check `JIRA_EMAIL` is correct
- Regenerate API token if needed
- Verify project key exists

### Issue: "OpenAI API error"

**Solutions**:
- Verify API key is correct
- Check you have credits/billing enabled
- Try a different model (set `OPENAI_MODEL=gpt-3.5-turbo` in `.env`)

### Issue: Vector store empty

**Solution**: Wait for initial sync to complete (check logs)

## Next Steps

1. **Test the API**: Try different queries to see how agents route requests
2. **Review Logs**: Check `logs/jira_assistant.log` for detailed information
3. **Customize**: Edit agent prompts in `src/agents/` for your use case
4. **Deploy**: See README.md for Docker deployment instructions

## API Documentation

Once running, visit:
- **API Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc

## Example Queries

### Search Queries
- "Find all high priority bugs"
- "Show me tickets about authentication"
- "Are there any performance issues reported?"

### Create Queries
- "Create a task to implement dark mode"
- "Report a bug: Users can't reset password"
- "Create a story for user profile page"

### Update Queries
- "Update PROJ-123 status to Done"
- "Change PROJ-456 priority to High"
- "Mark PROJ-789 as in progress"

## Support

If you encounter issues:

1. Check logs: `tail -f logs/jira_assistant.log`
2. Verify environment: `cat .env`
3. Test Jira connectivity: Visit `{JIRA_URL}` in browser
4. Test OpenAI: `curl https://api.openai.com/v1/models -H "Authorization: Bearer $OPENAI_API_KEY"`

---

Happy automating! 🚀

