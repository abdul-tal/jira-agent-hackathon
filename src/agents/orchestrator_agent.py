"""Orchestrator agent for routing and intent classification"""

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
    ("system", """You are an orchestrator for a Jira assistance chatbot. Your role is to classify user intent.

Classify the user's query into ONE of these intents:
- "search": User wants to find or search for existing tickets
- "create": User wants to create a new ticket
- "update": User wants to update an existing ticket
- "info": User wants general information or help

Respond with ONLY the intent word (search, create, update, or info), nothing else.

Examples:
- "Find tickets about login issues" -> search
- "Create a ticket for bug in payment" -> create
- "Update ticket PROJ-123 status" -> update
- "How do I use Jira?" -> info
- "Is there a ticket for API timeout?" -> search
- "I need to report a new bug" -> create"""),
    ("user", "{query}")
])


def orchestrator_node(state: AgentState) -> AgentState:
    """
    Classify user intent and route appropriately
    
    Args:
        state: Current agent state
    
    Returns:
        Updated state with intent classification
    """
    logger.info("Orchestrator: Classifying intent")
    
    query = state["user_query"]
    
    try:
        chain = ORCHESTRATOR_PROMPT | llm
        response = chain.invoke({"query": query})
        intent = response.content.strip().lower()
        
        # Validate intent
        if intent not in ["search", "create", "update", "info"]:
            logger.warning(f"Invalid intent '{intent}', defaulting to 'search'")
            intent = "search"
        
        state["intent"] = intent
        logger.info(f"Orchestrator: Classified as '{intent}'")
        
    except Exception as e:
        logger.error(f"Orchestrator error: {e}")
        state["intent"] = "search"  # Default fallback
    
    return state

