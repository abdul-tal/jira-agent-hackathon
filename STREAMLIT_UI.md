# Streamlit UI for Jira Assistant

Beautiful chat interface for interacting with your Jira Assistant chatbot.

## 🎨 Features

- **💬 Chat Interface**: Natural conversation with your Jira assistant
- **🔍 Search Results**: Visual display of similar tickets with similarity scores
- **✅ Ticket Creation**: See newly created tickets with all details
- **📊 System Status**: Real-time API health and statistics
- **🎨 Beautiful Design**: Clean, modern UI with Jira-inspired colors
- **💡 Help Section**: Built-in examples and usage guide
- **🗑️ Chat History**: Persistent conversation with clear history option

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# If not already installed
pip install streamlit==1.41.1
```

### 2. Start the API Server (Required)

```bash
# Terminal 1: Start the FastAPI backend
python main.py
```

The API should be running on `http://localhost:8000`

### 3. Start the Streamlit UI

```bash
# Terminal 2: Start the UI
streamlit run streamlit_app.py
```

The UI will open automatically in your browser at `http://localhost:8501`

## 📖 How to Use

### Search for Tickets

Type natural language queries:
- "Find tickets about login issues"
- "Show me bugs related to payment"
- "Search for authentication problems"

The UI will display:
- ✅ Similar tickets found
- 📊 Similarity scores (% match)
- 🎫 Ticket details (key, summary, description, status, priority)

### Create Tickets

Request ticket creation:
- "Create a bug for payment timeout"
- "Add a task to implement dark mode"
- "Report issue with API response time"

The UI will show:
- ✅ Success message
- 🎫 Created ticket with key (e.g., SCRUM-123)
- 📝 All ticket details

### Update Tickets

Update existing tickets:
- "Update SCRUM-123 priority to High"
- "Change status of SCRUM-456 to Done"
- "Mark SCRUM-789 as in progress"

### Ask Questions

General questions:
- "How can you help me?"
- "What can I do with this assistant?"

## 🎨 UI Components

### Header
- Application title and description
- Clean, modern design

### Sidebar
- **System Status**:
  - API connection indicator (✅/❌)
  - Total tickets indexed
  - Vector dimension
- **Help Section**:
  - Example queries
  - Usage instructions
- **Clear Chat**: Reset conversation

### Main Chat Area
- **User Messages**: Blue background
- **Assistant Messages**: Gray background
- **Ticket Cards**: 
  - Similarity scores (for search results)
  - Status badges (color-coded)
  - Priority indicators
  - Truncated descriptions

### Input Area
- Text input field
- Send button
- Real-time processing indicator

## 🛠️ Configuration

### API URL

Edit `streamlit_app.py` if your API runs on a different port:

```python
# Default
API_BASE_URL = "http://localhost:8000"

# Custom port
API_BASE_URL = "http://localhost:9000"
```

### Styling

Custom CSS is included in the app. Modify the `st.markdown()` section to change:
- Colors
- Fonts
- Spacing
- Card designs

## 🔍 Features in Detail

### Real-Time Health Check

The sidebar continuously monitors API health:
- ✅ Green: API is connected and working
- ❌ Red: API is down or unreachable

### Statistics Display

Shows live stats from the vector store:
- Number of tickets indexed
- Vector dimension (384 for all-MiniLM-L6-v2)

### Ticket Display

**Search Results:**
```
┌─────────────────────────────────┐
│ SCRUM-123         [85% Match]   │
│ Login timeout issue             │
│ Users experiencing timeouts...  │
│ [In Progress] Priority: High    │
└─────────────────────────────────┘
```

**Created Tickets:**
```
┌─────────────────────────────────┐
│ ✅ Ticket Created:              │
│ SCRUM-456                       │
│ Payment processing bug          │
│ Payment fails after 30 secs...  │
│ [To Do] Priority: Medium        │
└─────────────────────────────────┘
```

### Chat History

- Persists within session
- Scrollable conversation
- Color-coded messages
- Clear history button

## 🎯 Example Workflows

### Workflow 1: Search Before Creating

1. **User**: "Are there any tickets about login timeout?"
2. **Assistant**: Shows 3 similar tickets with 80%+ match
3. **User**: "Create a new ticket for login timeout on mobile"
4. **Assistant**: Creates ticket after checking for duplicates

### Workflow 2: Quick Create

1. **User**: "Create bug: API returns 500 error"
2. **Assistant**: Creates ticket immediately
3. **Result**: Shows newly created SCRUM-789

### Workflow 3: Update Ticket

1. **User**: "Update SCRUM-123 to High priority"
2. **Assistant**: Updates ticket successfully
3. **Result**: Confirmation message

## 🐛 Troubleshooting

### "API Disconnected" Error

**Problem**: Red indicator in sidebar

**Solutions**:
1. Check if API is running: `curl http://localhost:8000/health`
2. Start API: `python main.py`
3. Check port conflicts
4. Verify `.env` configuration

### "Request Timeout" Error

**Problem**: Request takes too long

**Causes**:
- First request (loading models)
- Large number of tickets
- Slow OpenAI API response

**Solution**: Wait 30 seconds and try again

### No Tickets Displayed

**Problem**: Search returns no results

**Causes**:
- Vector store empty (sync not run)
- No matching tickets
- Similarity threshold too high

**Solution**: 
1. Wait for initial sync to complete
2. Check API logs for sync status
3. Try broader search terms

### Streamlit Connection Error

**Problem**: Cannot connect to Streamlit

**Solution**:
```bash
# Kill existing Streamlit processes
pkill -f streamlit

# Restart
streamlit run streamlit_app.py
```

## 🎨 Customization

### Change Theme

Add `.streamlit/config.toml`:

```toml
[theme]
primaryColor = "#0052CC"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F5F5F5"
textColor = "#333333"
font = "sans serif"
```

### Add Features

The code is modular. You can add:
- User authentication
- Ticket filtering
- Advanced search options
- Export functionality
- Ticket analytics

### Modify Styling

Edit the CSS in `streamlit_app.py`:

```python
st.markdown("""
<style>
    /* Your custom CSS here */
</style>
""", unsafe_allow_html=True)
```

## 📊 Performance

- **Initial Load**: ~2 seconds
- **Message Response**: 3-5 seconds (includes AI processing)
- **UI Updates**: Instant (React-based)
- **Health Checks**: Every render

## 🔒 Security Notes

- UI connects to localhost API only
- No authentication built-in (add if deploying publicly)
- API key stored server-side only
- No sensitive data in UI state

## 🚀 Production Deployment

### Option 1: Streamlit Cloud

```bash
# Push to GitHub
git push origin main

# Deploy on streamlit.io
# Point to: streamlit_app.py
```

### Option 2: Docker

```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8501
CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

## 📚 Resources

- [Streamlit Documentation](https://docs.streamlit.io)
- [FastAPI Docs](https://fastapi.tiangolo.com)
- [Jira Assistant API Docs](http://localhost:8000/docs)

## 🎯 Next Steps

1. ✅ Start both servers (API + UI)
2. 🔍 Try searching for tickets
3. ✏️ Create a test ticket
4. 📊 Monitor statistics
5. 🎨 Customize the UI to your needs

---

**Enjoy your beautiful Jira Assistant interface!** 🎉

