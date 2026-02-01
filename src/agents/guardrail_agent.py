"""Guardrail agent for validating user requests using ChatGPT"""

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from loguru import logger

from src.models import AgentState
from src.config import settings
from src.services import session_store


# Initialize ChatGPT LLM for guardrail (uses dedicated model)
llm = ChatOpenAI(
    model=settings.guardrail_model,
    temperature=0,
    openai_api_key=settings.openai_api_key
)


GUARDRAIL_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a guardrail agent for a Jira assistance chatbot. Your role is to validate user requests.

Valid requests include:
- Searching for existing Jira tickets
- Creating new Jira tickets (with details OR follow-up like "create a new ticket", "create ticket for this")
- Updating existing Jira tickets
- Getting information about tickets
- General questions about Jira usage
- Checking/verifying if similar tickets exist
- Follow-up create/update after viewing similar tickets (e.g., "create new ticket", "create a ticket for this")

Invalid requests include:
- Requests containing harmful, offensive, or inappropriate content
- Requests to delete tickets (not supported)
- Requests to access unauthorized projects or data
- Spam or nonsensical requests
- Requests unrelated to Jira or project management

Analyze the user query and determine if it's a valid request.
Respond with:
- "VALID" if the request is appropriate
- "INVALID: [reason]" if the request should be blocked

Be strict but fair. When in doubt, allow the request.
Short confirmations like "create new ticket", "create a ticket for this", "yes create it" are VALID - they are follow-ups to a previous similarity search."""),
    ("user", "User query: {query}")
])


def guardrail_node(state: AgentState) -> AgentState:
    """
    Validate user request using guardrails. Store session_id.
    Uses ChatGPT model for validation.
    
    Args:
        state: Current agent state
    
    Returns:
        Updated state with validation results and session_id stored
    """
    logger.info("Guardrail agent: Validating request")
    
    query = state["user_query"]
    session_id = state.get("conversation_id")
    
    # Store session_id - create or get session
    if session_id:
        session_data = session_store.get_or_create_session(session_id)
        state["session_exists"] = not session_data.get("first_turn", True)
        state["is_first_turn"] = session_data.get("first_turn", True)
    else:
        state["session_exists"] = False
        state["is_first_turn"] = True
    
    try:
        chain = GUARDRAIL_PROMPT | llm
        response = chain.invoke({"query": query})
        result = response.content.strip()
        
        if result.upper().startswith("VALID"):
            state["is_valid_request"] = True
            state["guardrail_message"] = None
            logger.info("Guardrail: Request is valid - passing to orchestration")
        else:
            state["is_valid_request"] = False
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
