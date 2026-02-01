"""Streamlit UI for Jira Assistant Chatbot"""

import streamlit as st
import requests
from datetime import datetime
from typing import Dict, Any
import json

# Configuration
API_BASE_URL = "http://localhost:8000"

# Page configuration
st.set_page_config(
    page_title="Jira Assistant",
    page_icon="🎫",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    /* Main container background */
    .stApp {
        background-color: #FFFFFF;
    }
    
    /* Header styling */
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #0052CC;
        text-align: center;
        margin-bottom: 1rem;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
    }
    
    /* Chat messages */
    .chat-message {
        padding: 1.2rem;
        border-radius: 0.8rem;
        margin-bottom: 1rem;
        border-left: 5px solid;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .user-message {
        background-color: #E3F2FD !important;
        border-left-color: #2196F3 !important;
        color: #1565C0 !important;
    }
    
    .user-message strong {
        color: #0D47A1 !important;
        font-size: 1.1rem;
    }
    
    .assistant-message {
        background-color: #F5F5F5 !important;
        border-left-color: #0052CC !important;
        color: #212121 !important;
    }
    
    .assistant-message strong {
        color: #0052CC !important;
        font-size: 1.1rem;
    }
    
    /* Ticket cards */
    .ticket-card {
        padding: 1.2rem;
        border: 2px solid #E0E0E0;
        border-radius: 0.8rem;
        margin: 0.8rem 0;
        background-color: #FFFFFF !important;
        box-shadow: 0 2px 6px rgba(0,0,0,0.08);
        color: #212121 !important;
    }
    
    .ticket-key {
        font-weight: bold;
        color: #0052CC !important;
        font-size: 1.2rem;
    }
    
    .similarity-score {
        background-color: #4CAF50 !important;
        color: white !important;
        padding: 0.3rem 0.6rem;
        border-radius: 0.4rem;
        font-size: 0.85rem;
        font-weight: 600;
    }
    
    .status-badge {
        padding: 0.3rem 0.8rem;
        border-radius: 0.4rem;
        font-size: 0.9rem;
        font-weight: 600;
        color: white !important;
    }
    
    /* Ticket card text */
    .ticket-card h4 {
        color: #212121 !important;
        margin: 0.5rem 0;
    }
    
    .ticket-card p {
        color: #424242 !important;
    }
    
    /* Button styling */
    .stButton>button {
        width: 100%;
        background-color: #0052CC !important;
        color: white !important;
        border: none;
        padding: 0.6rem 1rem;
        font-size: 1rem;
        font-weight: 600;
        border-radius: 0.5rem;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        background-color: #0747A6 !important;
        box-shadow: 0 4px 8px rgba(0,82,204,0.3);
        transform: translateY(-2px);
    }
    
    /* Input field */
    .stTextInput input, .stChatInput textarea {
        border: 2px solid #E0E0E0 !important;
        border-radius: 0.5rem !important;
        padding: 0.8rem !important;
        font-size: 1rem !important;
        color: #212121 !important;
        background-color: #FFFFFF !important;
        caret-color: #0052CC !important;  /* Visible cursor */
    }
    
    .stTextInput input:focus, .stChatInput textarea:focus {
        border-color: #0052CC !important;
        box-shadow: 0 0 0 2px rgba(0,82,204,0.2) !important;
        outline: none !important;
    }
    
    .stTextInput input::placeholder, .stChatInput textarea::placeholder {
        color: #9E9E9E !important;
    }
    
    /* Chat input specific */
    .stChatInput {
        border: none !important;
        background-color: #F8F9FA !important;
        padding: 1rem !important;
        border-radius: 0.8rem !important;
        margin-top: 1rem !important;
    }
    
    .stChatInput > div {
        background-color: #FFFFFF !important;
        border-radius: 0.5rem !important;
    }
    
    /* Sidebar styling */
    .css-1d391kg, [data-testid="stSidebar"] {
        background-color: #F8F9FA;
    }
    
    /* Ensure all text is visible */
    p, span, div {
        color: #212121;
    }
    
    /* Markdown headings */
    h1, h2, h3, h4, h5, h6 {
        color: #212121 !important;
    }
    
    /* Success/Error messages */
    .stSuccess {
        background-color: #E8F5E9 !important;
        color: #2E7D32 !important;
        border-left: 4px solid #4CAF50 !important;
    }
    
    .stError {
        background-color: #FFEBEE !important;
        color: #C62828 !important;
        border-left: 4px solid #F44336 !important;
    }
    
    .stWarning {
        background-color: #FFF3E0 !important;
        color: #E65100 !important;
        border-left: 4px solid #FF9800 !important;
    }
</style>
""", unsafe_allow_html=True)


def check_api_health() -> bool:
    """Check if API is running"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=2)
        return response.status_code == 200
    except:
        return False


def get_api_stats() -> Dict[str, Any]:
    """Get API statistics"""
    try:
        response = requests.get(f"{API_BASE_URL}/stats", timeout=5)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return {}


def send_chat_message(question: str, session_id: str) -> Dict[str, Any]:
    """Send message to chatbot API"""
    try:
        url = f"{API_BASE_URL}/chat"
        payload = {
            "session_id": session_id,
            "question": question
        }
        
        # Debug logging
        print(f"🔵 Sending request to: {url}")
        print(f"🔵 Payload: {payload}")
        
        response = requests.post(
            url,
            json=payload,
            timeout=60
        )
        
        print(f"🔵 Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"🔵 Response received: {len(str(result))} bytes")
            return result
        else:
            error_msg = f"API Error: {response.status_code}"
            print(f"❌ {error_msg}")
            return {"error": error_msg}
    except requests.exceptions.Timeout:
        error_msg = "Request timeout. The AI is thinking... please try again."
        print(f"❌ {error_msg}")
        return {"error": error_msg}
    except Exception as e:
        error_msg = f"Connection error: {str(e)}"
        print(f"❌ {error_msg}")
        return {"error": error_msg}


def send_chat_message_stream(question: str, session_id: str, status_placeholder):
    """Send message to chatbot API with streaming updates"""
    try:
        url = f"{API_BASE_URL}/chat/stream"
        payload = {
            "session_id": session_id,
            "question": question
        }
        
        print(f"🔵 Starting stream to: {url}")
        
        final_result = None
        events_received = []
        
        with requests.post(url, json=payload, stream=True, timeout=60) as response:
            if response.status_code != 200:
                return {"error": f"API Error: {response.status_code}"}
            
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        try:
                            event_data = json.loads(line[6:])  # Remove 'data: ' prefix
                            event_type = event_data.get('event', '')
                            message = event_data.get('message', '')
                            
                            events_received.append(event_type)
                            
                            # Update status placeholder with current progress
                            if event_type == 'start':
                                status_placeholder.info(f"🚀 {message}")
                            elif event_type == 'guardrail':
                                status_placeholder.info(f"{message}")
                            elif event_type == 'orchestrator':
                                status_placeholder.info(f"{message}")
                            elif event_type == 'similarity':
                                status_placeholder.info(f"{message}")
                            elif event_type == 'similarity_found':
                                status_placeholder.success(f"{message}")
                            elif event_type == 'similarity_not_found':
                                status_placeholder.warning(f"{message}")
                            elif event_type == 'ticket_created':
                                status_placeholder.success(f"{message}")
                            elif event_type == 'ticket_updated':
                                status_placeholder.success(f"{message}")
                            elif event_type == 'complete':
                                final_result = event_data.get('result')
                                status_placeholder.success("✅ Processing complete!")
                            elif event_type == 'error':
                                status_placeholder.error(f"❌ Error: {message}")
                                return {"error": message}
                            
                            # Small delay for smooth UI updates
                            import time
                            time.sleep(0.2)
                            
                        except json.JSONDecodeError:
                            continue
        
        print(f"🟢 Stream complete. Events: {events_received}")
        
        if final_result:
            return final_result
        else:
            return {"error": "No result received from stream"}
            
    except requests.exceptions.Timeout:
        return {"error": "Request timeout"}
    except Exception as e:
        print(f"❌ Stream error: {e}")
        return {"error": str(e)}


def display_ticket_card(ticket: Dict[str, Any], show_similarity: bool = True):
    """Display a ticket in a card format"""
    import html as html_module
    
    # Determine status color
    status = ticket.get('status', 'Unknown')
    if status == 'Done':
        status_color = '#4CAF50'
    elif 'Progress' in status:
        status_color = '#FF9800'
    elif status == 'To Do':
        status_color = '#2196F3'
    else:
        status_color = '#9E9E9E'
    
    # Get similarity badge
    similarity_badge = ""
    if show_similarity and ticket.get('similarity_score'):
        similarity_badge = f"<span class='similarity-score'>{ticket.get('similarity_score', 0)*100:.0f}% Match</span>"
    
    # Get and escape description
    description = ticket.get('description', '').strip()
    if not description:
        description = "<em style='color: #999;'>No description provided</em>"
    else:
        # Truncate long descriptions and escape HTML
        if len(description) > 200:
            description = html_module.escape(description[:200]) + '...'
        else:
            description = html_module.escape(description)
    
    # Escape ticket data to prevent HTML injection
    ticket_key = html_module.escape(str(ticket.get('key', '')))
    summary = html_module.escape(str(ticket.get('summary', '')))
    priority = html_module.escape(str(ticket.get('priority', 'None')))
    status_escaped = html_module.escape(status)
    
    with st.container():
        st.markdown(f"""
        <div class="ticket-card">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.8rem;">
                <span class="ticket-key">{ticket_key}</span>
                {similarity_badge}
            </div>
            <h4 style="color: #212121 !important; margin: 0.5rem 0; font-size: 1.1rem;">{summary}</h4>
            <div style="color: #424242 !important; margin: 0.8rem 0; line-height: 1.5; background-color: #FFFFFF !important;">
                {description}
            </div>
            <div style="display: flex; gap: 1rem; margin-top: 1rem; align-items: center;">
                <span class="status-badge" style="background-color: {status_color} !important; color: #FFFFFF !important;">
                    {status_escaped}
                </span>
                <span style="color: #424242 !important; font-weight: 500;">
                    Priority: <strong style="color: #212121 !important;">{priority}</strong>
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)


def initialize_session_state():
    """Initialize session state variables"""
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'conversation_id' not in st.session_state:
        st.session_state.conversation_id = datetime.now().strftime("%Y%m%d_%H%M%S")


def main():
    """Main application"""
    initialize_session_state()
    
    # Header
    st.markdown('<div class="main-header">🎫 Jira Assistant</div>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; color: #424242 !important; font-size: 1.1rem; margin-bottom: 2rem;">Your AI-powered Jira ticket assistant</p>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("📊 System Status")
        
        # API Health Check
        api_healthy = check_api_health()
        if api_healthy:
            st.success("✅ API Connected")
        else:
            st.error("❌ API Disconnected")
            st.warning("Please start the API server:\n```bash\npython main.py\n```")
        
        # API Stats
        if api_healthy:
            stats = get_api_stats()
            if stats:
                st.metric("Total Tickets Indexed", stats.get('total_tickets', 0))
                st.metric("Vector Dimension", stats.get('dimension', 0))
        
        st.divider()
        
        # Help Section
        st.header("💡 How to Use")
        st.markdown("""
        **Search for tickets:**
        - "Find tickets about login issues"
        - "Show me bugs related to API"
        
        **Create tickets:**
        - "Create a bug for payment timeout"
        - "Add a task to implement dark mode"
        
        **Update tickets:**
        - "Update SCRUM-123 to High priority"
        - "Change status of SCRUM-456 to Done"
        """)
        
        st.divider()
        
        # Clear Chat
        if st.button("🗑️ Clear Chat History"):
            st.session_state.messages = []
            st.rerun()
    
    # Main Chat Interface
    st.markdown("---")
    
    # Display chat history
    for message in st.session_state.messages:
        # Skip debug messages (they're logged to terminal only)
        if message.get("role") == "debug":
            import sys
            print(message["content"], file=sys.stderr)
            continue
            
        if message["role"] == "user":
            st.markdown(f"""
            <div class="chat-message user-message">
                <strong style="color: #0D47A1 !important; font-size: 1.05rem;">👤 You:</strong><br>
                <span style="color: #1565C0 !important; font-size: 1rem; line-height: 1.6;">{message["content"]}</span>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="chat-message assistant-message">
                <strong style="color: #0052CC !important; font-size: 1.05rem;">🤖 Assistant:</strong><br>
                <span style="color: #212121 !important; font-size: 1rem; line-height: 1.6;">{message["content"]}</span>
            </div>
            """, unsafe_allow_html=True)
            
            # Display tickets based on type
            if message.get("tickets"):
                ticket_type = message.get("type", "SIMILAR")
                
                if ticket_type == "SIMILAR":
                    st.markdown('<h3 style="color: #212121 !important; margin: 1rem 0;">🔍 Similar Tickets Found:</h3>', unsafe_allow_html=True)
                    for ticket in message["tickets"]:
                        display_ticket_card(ticket, show_similarity=True)
                
                elif ticket_type == "CREATED":
                    st.markdown('<h3 style="color: #212121 !important; margin: 1rem 0;">✅ Ticket Created:</h3>', unsafe_allow_html=True)
                    for ticket in message["tickets"]:
                        display_ticket_card(ticket, show_similarity=False)
                        st.success(f"🎉 Successfully created ticket: **{ticket['key']}**")
                
                elif ticket_type == "UPDATED":
                    st.markdown('<h3 style="color: #212121 !important; margin: 1rem 0;">🔄 Ticket Updated:</h3>', unsafe_allow_html=True)
                    for ticket in message["tickets"]:
                        display_ticket_card(ticket, show_similarity=False)
                        st.success(f"✨ Successfully updated ticket: **{ticket['key']}**")
    
    # Chat Input (handles Enter key naturally)
    st.markdown("---")
    
    user_input = st.chat_input(
        placeholder="Ask me anything about Jira tickets... (Press Enter to send)",
        key="chat_input"
    )
    
    # Handle message submission (triggered by Enter or Send button)
    if user_input:
        if not api_healthy:
            st.error("⚠️ API is not connected. Please start the server first.")
        else:
            # Add user message to history
            st.session_state.messages.append({
                "role": "user",
                "content": user_input
            })
            
            # Create a placeholder for status updates
            status_placeholder = st.empty()
            
            # Send to API with streaming updates
            response = send_chat_message_stream(
                user_input, 
                st.session_state.conversation_id,
                status_placeholder
            )
            
            # Clear status placeholder
            status_placeholder.empty()
            
            if "error" in response and response["error"]:
                assistant_message = f"❌ Error: {response['error']}"
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": assistant_message
                })
            else:
                # Add assistant response
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response.get("message", "No response"),
                    "tickets": response.get("tickets", []),
                    "type": response.get("type", "SIMILAR")
                })
            
            # Rerun to update UI
            st.rerun()
    
    # Footer
    st.markdown("---")
    st.markdown(
        '<p style="text-align: center; color: #757575 !important; font-size: 0.9rem;">'
        'Powered by LangGraph, OpenAI & FAISS | '
        f'Conversation ID: {st.session_state.conversation_id}'
        '</p>',
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()

