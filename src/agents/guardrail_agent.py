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

Be strict but fair. When in doubt, allow the request."""),
    ("user", "User query: {query}")
])


async def guardrail_node(state: AgentState, config: dict = None) -> AgentState:
    """
    Validate user request using guardrails
    
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
    
    try:
        # Check with LLM
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

