"""Orchestrator agent for routing and intent classification"""

import json
import re
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from loguru import logger

from src.models import AgentState
from src.config import settings


# Initialize LLM
llm = ChatOpenAI(
    model=settings.openai_model,
    temperature=0,
    openai_api_key=settings.openai_api_key
)


ORCHESTRATOR_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are an orchestrator for a Jira assistance chatbot with conversation memory. Your role is to classify user intent and extract relevant information, using conversation context when available.

Classify the user's query into ONE of these intents:
- "search": User wants to find or search for existing tickets
- "create": User wants to create a new ticket
- "update": User wants to update an existing ticket
- "info": User wants general information or help

**IMPORTANT**: If the user references previous conversation (e.g., "update that ticket", "the one we just created", "add a comment to it"), use the conversation history to resolve the reference and extract the ticket key.

For CREATE intent, also extract:
- summary: A concise title for the ticket (10-15 words max) - extract the main issue/topic
- description: Full detailed description including ALL details from the user's query (symptoms, error messages, context, steps, etc.)
- issue_type: Task, Bug, Story, or Epic (infer from context - use "Bug" if error/issue mentioned, default: Task)
- project_key: Project key if mentioned (default: SCRUM)

IMPORTANT: For description, include the complete details from the user's message, not just a brief summary.

For UPDATE intent, also extract:
- issue_key: The Jira ticket key (e.g., PROJ-123) - look in conversation history if not in current query
- comment: The update text or comment to add

Respond in JSON format:
{{
  "intent": "create|update|search|info",
  "ticket_data": {{
    "summary": "...",
    "description": "...",
    "issue_type": "Task",
    "project_key": "SCRUM",
    "issue_key": "PROJ-123",
    "comment": "..."
  }}
}}

Only include relevant fields in ticket_data based on the intent.

Examples:
- "Create a ticket for login bug with OAuth2. Users getting 401 error" -> {{"intent": "create", "ticket_data": {{"summary": "Fix login authentication bug with OAuth2", "description": "Users are unable to login with OAuth2 credentials. Getting 401 error when attempting authentication.", "issue_type": "Bug", "project_key": "SCRUM"}}}}
- "Create task to implement user dashboard" -> {{"intent": "create", "ticket_data": {{"summary": "Implement user dashboard", "description": "Need to create a user dashboard showing account statistics and recent activity", "issue_type": "Task", "project_key": "SCRUM"}}}}
- "Update PROJ-123 with progress update" -> {{"intent": "update", "ticket_data": {{"issue_key": "PROJ-123", "comment": "Progress update"}}}}
- With history showing "Created ticket SCRUM-42": "Update it with comment: fixed" -> {{"intent": "update", "ticket_data": {{"issue_key": "SCRUM-42", "comment": "fixed"}}}}
- "Find tickets about API" -> {{"intent": "search", "ticket_data": {{}}}}"""),
    ("user", "{query}")
])


async def orchestrator_node(state: AgentState, config: dict = None) -> AgentState:
    """
    Classify user intent and extract ticket data with conversation context
    
    Args:
        state: Current agent state with conversation history
        config: LangGraph config containing runtime context
    
    Returns:
        Updated state with intent classification and ticket data
    """
    logger.info("Orchestrator: Classifying intent and extracting data")
    
    # Emit event if queue is available
    event_queue = config.get("configurable", {}).get("event_queue") if config else None
    if event_queue:
        await event_queue.put({'event': 'orchestrator', 'message': '🧠 Analyzing intent...'})
    
    query = state["user_query"]
    messages = state.get("messages", [])
    
    try:
        # Build context from conversation history
        context_parts = []
        if len(messages) > 1:  # More than just current message
            context_parts.append("Previous conversation:")
            # Get last few messages (excluding current query)
            for msg in messages[-6:-1]:  # Last 5 messages before current
                role = "User" if msg.type == "human" else "Assistant"
                context_parts.append(f"{role}: {msg.content[:100]}")
            context_parts.append("\nCurrent query:")
        
        # Combine context with query
        full_query = "\n".join(context_parts) + f"\n{query}" if context_parts else query
        
        chain = ORCHESTRATOR_PROMPT | llm
        response = chain.invoke({"query": full_query})
        
        # Parse JSON response
        content = response.content.strip()
        
        # Try to extract JSON from response
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
            intent = data.get("intent", "search").lower()
            ticket_data = data.get("ticket_data", {})
        else:
            # Fallback: treat response as just intent
            intent = content.lower()
            ticket_data = {}
        
        # Validate intent
        if intent not in ["search", "create", "update", "info"]:
            logger.warning(f"Invalid intent '{intent}', defaulting to 'search'")
            intent = "search"
        
        # Log extracted data for debugging
        logger.info(f"Orchestrator: Classified as '{intent}'")
        logger.info(f"Orchestrator: Ticket data - {ticket_data}")
        
        # Validate create/update ticket data
        if intent == "create":
            if not ticket_data.get("summary"):
                logger.warning("Orchestrator: No summary extracted, will use user query as fallback")
            if not ticket_data.get("description"):
                logger.warning("Orchestrator: No description extracted, will use user query as fallback")
        
        state["intent"] = intent
        state["ticket_data"] = ticket_data
        
        # Emit thinking complete event
        if event_queue:
            await event_queue.put({'event': 'thinking_complete', 'message': '💡 Analysis complete', 'intent': intent})
        
    except Exception as e:
        logger.error(f"Orchestrator error: {e}")
        state["intent"] = "search"  # Default fallback
        state["ticket_data"] = {}
    
    return state

