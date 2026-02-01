"""Orchestrator agent for routing based on keywords and session state"""

import re
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from loguru import logger

from src.models import AgentState
from src.config import settings

# Keywords for routing decisions
JIRA_CREATE_UPDATE_KEYWORDS = [
    r"\bcreate\b", r"\bcreat(e|ing|ed)\b", r"\badd\b", r"\bnew\s+ticket\b",
    r"\bupdate\b", r"\bupdat(e|ing|ed)\b", r"\bmodify\b", r"\bchange\b",
    r"\bedit\b", r"\bset\s+(status|priority)\b", r"\bmark\s+as\b",
]

SIMILARITY_VERIFY_KEYWORDS = [
    r"\bcheck\b", r"\bverify\b", r"\bsearch\b", r"\bfind\b", r"\blook\s*(up|for)\b",
    r"\bexist(s|ing)?\b", r"\bsimilar\b", r"\bduplicate\b", r"\bmatch(es|ing)?\b",
    r"\bis\s+there\b", r"\bany\s+ticket\b", r"\bexisting\b", r"\bhistorical\b",
]

# Initialize LLM
llm = ChatOpenAI(
    model=settings.openai_model,
    temperature=0,
    openai_api_key=settings.openai_api_key
)


ORCHESTRATOR_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are an orchestrator for a Jira assistance chatbot. Your role is to classify user intent and decide routing.

Routing rules:
1. If user explicitly wants to CREATE or UPDATE a ticket (e.g., "create a new ticket", "update PROJ-123", "add a bug") -> route to "jira"
2. If user wants to CHECK, VERIFY, or SEARCH for similar tickets (e.g., "check if similar exists", "find tickets about X", "verify duplicates") -> route to "similarity"
3. If this is the FIRST message in a session and user describes an issue (without explicit create/update) -> route to "similarity" (to check historical data first)
4. If user previously saw similar tickets and now says "create new one" or "create ticket" -> route to "jira"

Respond with ONLY one word: "similarity", "jira", or "final"
- "similarity": Call similarity agent to search/verify tickets
- "jira": Call Jira agent to create or update ticket
- "final": General info/help, no agent needed"""),
    ("user", """User query: {query}

Session context:
- Is first turn in session: {is_first_turn}
- Session already existed: {session_exists}

Your routing decision (similarity/jira/final):""")
])


def _has_keywords(text: str, patterns: list) -> bool:
    """Check if text matches any of the keyword patterns."""
    text_lower = text.lower().strip()
    for pattern in patterns:
        if re.search(pattern, text_lower, re.IGNORECASE):
            return True
    return False


def orchestrator_node(state: AgentState) -> AgentState:
    """
    Route to appropriate agent based on:
    1. Keywords (create/update -> jira; check/verify -> similarity)
    2. Session state (first turn always -> similarity)
    3. LLM fallback for ambiguous cases
    """
    logger.info("Orchestrator: Deciding routing")
    
    query = state["user_query"]
    is_first_turn = state.get("is_first_turn", True)
    session_exists = state.get("session_exists", False)
    
    route_to = None
    
    # Rule 1: First turn always goes to similarity (check historical data)
    if is_first_turn:
        route_to = "similarity"
        state["intent"] = "search"
        logger.info("Orchestrator: First turn -> similarity agent")
    
    # Rule 2: Explicit create/update keywords -> Jira (when session exists or standalone)
    elif _has_keywords(query, JIRA_CREATE_UPDATE_KEYWORDS):
        route_to = "jira"
        if _has_keywords(query, [r"\bupdate\b", r"\bupdat(e|ing|ed)\b", r"\bmodify\b", r"\bedit\b"]):
            state["intent"] = "update"
        else:
            state["intent"] = "create"
        logger.info(f"Orchestrator: Create/update keywords -> jira agent (intent={state['intent']})")
    
    # Rule 3: Check/verify keywords -> Similarity
    elif _has_keywords(query, SIMILARITY_VERIFY_KEYWORDS):
        route_to = "similarity"
        state["intent"] = "search"
        logger.info("Orchestrator: Check/verify keywords -> similarity agent")
    
    # Rule 4: Use LLM for ambiguous cases
    if route_to is None:
        try:
            chain = ORCHESTRATOR_PROMPT | llm
            response = chain.invoke({
                "query": query,
                "is_first_turn": is_first_turn,
                "session_exists": session_exists,
            })
            route_to = response.content.strip().lower().split()[0]
            
            if route_to not in ["similarity", "jira", "final"]:
                route_to = "similarity"  # Default to similarity for safety
            
            if route_to == "jira":
                state["intent"] = "create"  # Default to create
            elif route_to == "similarity":
                state["intent"] = "search"
            
            logger.info(f"Orchestrator: LLM decided -> {route_to}")
        except Exception as e:
            logger.error(f"Orchestrator LLM error: {e}")
            route_to = "similarity"
            state["intent"] = "search"
    
    state["route_to"] = route_to
    return state
