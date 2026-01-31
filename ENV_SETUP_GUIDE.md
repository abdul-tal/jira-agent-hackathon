# Environment Setup Guide

## 🔐 How Secrets Management Works

This project uses **environment variables** to keep your secrets safe. Here's how it works:

```
┌─────────────────┐
│   .env file     │  ← Your actual secrets (NEVER commit to git)
│ (gitignored)    │
└────────┬────────┘
         │
         │ Pydantic reads automatically
         ▼
┌─────────────────┐
│  settings.py    │  ← Schema definition (safe to commit)
│  (in git)       │
└────────┬────────┘
         │
         │ Used by application
         ▼
┌─────────────────┐
│  Your App       │  ← Access via settings.openai_api_key, etc.
└─────────────────┘
```

## 📝 Step-by-Step Setup

### Step 1: Copy the Template

```bash
cd jira-hackathon
cp .env.example .env
```

### Step 2: Get Your API Keys

#### OpenAI API Key

1. Go to https://platform.openai.com/api-keys
2. Click **"Create new secret key"**
3. Copy the key (starts with `sk-proj-` or `sk-`)
4. Save it securely - you won't see it again!

#### Jira API Token

1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Click **"Create API token"**
3. Give it a name (e.g., "Jira Assistant")
4. Copy the token
5. Save it securely

#### Jira Project Details

- **JIRA_URL**: Your Jira instance URL (e.g., `https://mycompany.atlassian.net`)
- **JIRA_EMAIL**: Your Jira account email
- **JIRA_PROJECT_KEY**: Your project key (e.g., `PROJ`, `DEV`, `BUG`)

### Step 3: Edit .env File

Open `.env` in your favorite editor and fill in your secrets:

```bash
nano .env  # or code .env, vim .env, etc.
```

**Your .env should look like this:**

```env
# OpenAI Configuration
OPENAI_API_KEY=sk-proj-YOUR_ACTUAL_KEY_HERE
OPENAI_MODEL=gpt-4-turbo-preview
EMBEDDING_MODEL=text-embedding-3-small

# Jira Configuration
JIRA_URL=https://mycompany.atlassian.net
JIRA_EMAIL=john.doe@mycompany.com
JIRA_API_TOKEN=YOUR_ACTUAL_JIRA_TOKEN_HERE
JIRA_PROJECT_KEY=PROJ

# Vector Store Configuration
VECTOR_STORE_PATH=./data/vector_store
FAISS_INDEX_NAME=jira_tickets

# Sync Job Configuration
SYNC_INTERVAL_HOURS=24
SYNC_ON_STARTUP=true

# Server Configuration
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO

# Agent Configuration
MAX_SIMILARITY_RESULTS=5
SIMILARITY_THRESHOLD=0.7
MAX_RETRIES=3
```

### Step 4: Validate Configuration

Before starting the application, validate your `.env`:

```bash
python validate_env.py
```

**Expected output:**

```
🔍 Validating .env configuration...

✅ .env file exists

🔑 Checking secrets:
  ✅ OPENAI_API_KEY: sk-proj-...xyz
  ✅ JIRA_URL: https://mycompany.atlassian.net
  ✅ JIRA_EMAIL: john.doe@mycompany.com
  ✅ JIRA_API_TOKEN: abcd...xyz
  ✅ JIRA_PROJECT_KEY: PROJ

⚙️  Configuration:
  • OpenAI Model: gpt-4-turbo-preview
  • Embedding Model: text-embedding-3-small
  • Sync Interval: 24 hours
  • Sync On Startup: True
  • Server Port: 8000
  • Max Similarity Results: 5
  • Similarity Threshold: 0.7

✨ Configuration is valid!

🚀 You can now start the application:
   python main.py
```

### Step 5: Start the Application

```bash
python main.py
```

## 🔍 How Pydantic Loads Environment Variables

The magic happens in `src/config/settings.py`:

```python
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",           # ← Reads from .env file
        case_sensitive=False       # ← OPENAI_API_KEY → openai_api_key
    )
    
    # Define what secrets we need
    openai_api_key: str  # ← REQUIRED (no default value)
    jira_api_token: str  # ← REQUIRED (no default value)
    
    # With defaults (optional in .env)
    port: int = 8000     # ← Will use 8000 if not in .env
```

**How it maps:**

| .env File | Python Code |
|-----------|-------------|
| `OPENAI_API_KEY=sk-...` | `settings.openai_api_key` |
| `JIRA_API_TOKEN=abc123` | `settings.jira_api_token` |
| `JIRA_URL=https://...` | `settings.jira_url` |
| `PORT=8000` | `settings.port` |

## ✅ Validation Features

The enhanced `settings.py` now includes:

### 1. Required Field Validation

```python
openai_api_key: str = Field(
    ...,  # ← The "..." means REQUIRED
    description="OpenAI API key"
)
```

If missing, you'll get a helpful error:

```
❌ OPENAI_API_KEY is required.
Get your key from https://platform.openai.com/api-keys
and add it to .env file
```

### 2. Format Validation

```python
@field_validator('openai_api_key')
def validate_openai_key(cls, v: str) -> str:
    if not v.startswith('sk-'):
        raise ValueError("OPENAI_API_KEY should start with 'sk-'")
    return v
```

### 3. Automatic Cleanup

- Strips whitespace from secrets
- Removes trailing slashes from URLs
- Uppercases project keys

## 🚫 What NOT to Do

### ❌ Never Commit Secrets

```bash
# BAD - Do NOT do this!
git add .env
git commit -m "Added my API keys"  # ← Your secrets are now public!
```

**Why?** Once committed to git, secrets are in the history forever, even if you delete them later.

### ❌ Never Hardcode Secrets

```python
# BAD - Do NOT do this!
openai_api_key = "sk-proj-abc123..."  # ← Hardcoded in code
```

**Always use:**

```python
# GOOD ✅
from src.config import settings
openai_api_key = settings.openai_api_key  # ← From .env
```

### ❌ Never Share .env File

Don't send `.env` file via:
- Email
- Slack/Teams
- Cloud storage
- Screenshots (keys are visible!)

**Instead:** Share `.env.example` as a template

## 🔒 Security Best Practices

### 1. Use .gitignore

Already configured in `.gitignore`:

```gitignore
# Environment
.env
.env.local
.env.*.local
```

### 2. Rotate Keys Regularly

- Change API keys every 3-6 months
- Rotate immediately if exposed
- Use different keys for dev/staging/production

### 3. Minimum Permissions

- **Jira Token**: Give only necessary permissions
- **OpenAI Key**: Set usage limits in OpenAI dashboard

### 4. Production Secrets

For production, use a secrets manager:
- AWS Secrets Manager
- Azure Key Vault
- HashiCorp Vault
- Google Secret Manager

## 🛠️ Troubleshooting

### Error: ".env file not found"

**Solution:**

```bash
cp .env.example .env
# Then edit .env with your secrets
```

### Error: "OPENAI_API_KEY should start with 'sk-'"

**Solution:** Check your OpenAI API key format. It should look like:
- `sk-proj-...` (new format)
- `sk-...` (old format)

### Error: "JIRA_API_TOKEN is required"

**Solution:** 

1. Get token from https://id.atlassian.com/manage-profile/security/api-tokens
2. Add to `.env` file: `JIRA_API_TOKEN=your_token_here`

### Error: Jira authentication failed

**Solutions:**

- Verify `JIRA_URL` is correct (no trailing slash)
- Check `JIRA_EMAIL` matches your Atlassian account
- Regenerate `JIRA_API_TOKEN` if expired
- Verify `JIRA_PROJECT_KEY` exists in your Jira

### Validate Your Configuration

Run this anytime:

```bash
python validate_env.py
```

## 📚 Additional Resources

- [Pydantic Settings Documentation](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- [OpenAI API Keys](https://platform.openai.com/api-keys)
- [Jira API Tokens](https://support.atlassian.com/atlassian-account/docs/manage-api-tokens-for-your-atlassian-account/)
- [12-Factor App Config](https://12factor.net/config)

## 🎯 Quick Reference

| File | Purpose | Commit to Git? |
|------|---------|----------------|
| `.env.example` | Template without secrets | ✅ Yes |
| `.env` | Your actual secrets | ❌ **NO!** |
| `settings.py` | Schema definition | ✅ Yes |
| `.gitignore` | Protects .env | ✅ Yes |
| `validate_env.py` | Validation script | ✅ Yes |

---

**Remember:** Keep your secrets secret! 🔐

