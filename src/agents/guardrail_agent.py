"""Guardrail agent for validating user requests"""

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


GUARDRAIL_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a guardrail agent for a Jira assistance chatbot. Your role is to validate user requests.

Valid requests include:
- Searching for existing Jira tickets
- Creating new Jira tickets with proper information
- Updating existing Jira tickets
- Getting information about tickets
- General questions about Jira usage
- Conversational queries and greetings

Invalid requests include:
- Requests containing harmful, offensive, or inappropriate content
- Requests to delete tickets (not supported)
- Requests to access unauthorized projects or data
- Spam or nonsensical requests
- Requests completely unrelated to work or project management

Analyze the user query and determine if it's a valid request.
Respond with:
- "VALID" if the request is appropriate
- "INVALID: [reason]" if the request should be blocked

Be permissive and allow conversational queries. When in doubt, allow the request."""),
    ("user", "User query: {query}")
])


async def guardrail_node(state: AgentState, config: dict = None) -> AgentState:
    """
    Validate user request using guardrails and handle simple conversational queries
    
    Args:
        state: Current agent state
        config: LangGraph config containing runtime context
    
    Returns:
        Updated state with validation results
    """
    logger.info("Guardrail agent: Validating request")
    
    # Emit event if queue is available
    event_queue = config.get("configurable", {}).get("event_queue") if config else None
    if event_queue:
        await event_queue.put({'event': 'guardrail', 'message': '🛡️ Validating request...'})
    
    query = state["user_query"]
    query_lower = query.lower().strip()
    
    # Handle simple greetings and conversational queries directly
    greetings = ["hi", "hello", "hey", "good morning", "good afternoon", "good evening", "greetings"]
    help_queries = ["help", "what can you do", "how can you help", "what do you do", "capabilities", "features"]
    
    # Check for simple greetings
    if query_lower in greetings or any(query_lower.startswith(g) for g in greetings):
        state["is_valid_request"] = False  # Will skip to end
        state["guardrail_message"] = "greeting_handled"
        state["final_response"] = (
            "Hello! 👋 I'm your Jira assistant. I can help you:\n\n"
            "- 🔍 **Search** for existing tickets\n"
            "- ➕ **Create** new tickets\n"
            "- ✏️ **Update** existing tickets\n\n"
            "What would you like to do today?"
        )
        logger.info("Guardrail: Handled greeting directly")
        
        # Emit completion event
        if event_queue:
            await event_queue.put({'event': 'greeting_handled', 'message': '👋 Greeting responded'})
        
        return state
    
    # Check for help/capability queries
    if any(help_word in query_lower for help_word in help_queries):
        state["is_valid_request"] = False  # Will skip to end
        state["guardrail_message"] = "help_handled"
        state["final_response"] = (
            "I'm your Jira assistant! Here's what I can do:\n\n"
            "🔍 **Search for tickets**\n"
            "   - \"Find tickets about login issues\"\n"
            "   - \"Show me all high priority bugs\"\n\n"
            "➕ **Create new tickets**\n"
            "   - \"Create a task for implementing dark mode\"\n"
            "   - \"Create a bug for the payment gateway error\"\n\n"
            "✏️ **Update existing tickets**\n"
            "   - \"Update SCRUM-42 with a comment: completed\"\n"
            "   - \"Add a comment to SCRUM-15\"\n\n"
            "Just ask me naturally, and I'll help you manage your Jira tickets!"
        )
        logger.info("Guardrail: Handled help query directly")
        
        # Emit completion event
        if event_queue:
            await event_queue.put({'event': 'help_handled', 'message': '💡 Help information provided'})
        
        return state
    
    try:
        # Check with LLM for other requests
        chain = GUARDRAIL_PROMPT | llm
        response = chain.invoke({"query": query})
        result = response.content.strip()
        
        if result.startswith("VALID"):
            state["is_valid_request"] = True
            state["guardrail_message"] = None
            logger.info("Guardrail: Request is valid")
        else:
            state["is_valid_request"] = False
            # Extract reason from "INVALID: reason"
            reason = result.split(":", 1)[1].strip() if ":" in result else "Request does not meet guidelines"
            state["guardrail_message"] = reason
            state["final_response"] = f"I cannot process this request. {reason}"
            logger.warning(f"Guardrail: Request blocked - {reason}")
        
    except Exception as e:
        logger.error(f"Guardrail agent error: {e}")
        # On error, default to allowing the request
        state["is_valid_request"] = True
        state["guardrail_message"] = None
    
    return state

