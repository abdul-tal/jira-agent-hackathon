"""LangGraph workflow for Jira assistance with Guardrail and Orchestration"""

from datetime import datetime
from typing import Literal
from langgraph.graph import StateGraph, END
from loguru import logger

from src.models import AgentState
from src.agents import orchestrator_node, guardrail_node, similarity_node, jira_node


def create_final_response_node(state: AgentState) -> AgentState:
    """
    Create final response for search/verify intents.
    Presents similar tickets to user and asks them to decide action (create/update).
    """
    logger.info("Creating final response")
    
    # Similarity agent may have already set final_response (no historical data)
    if state.get("final_response") and state.get("has_historical_data") is False:
        return state
    
    # If we came from orchestrator directly (route_to=final, info/help)
    route_to = state.get("route_to")
    if route_to == "final" and not state.get("similar_tickets"):
        state["final_response"] = (
            "I'm your Jira assistant! I can help you:\n"
            "- **Check/verify** if similar tickets exist (say 'check if there are tickets about X')\n"
            "- **Create** new tickets (say 'create a ticket for...')\n"
            "- **Update** existing tickets (say 'update PROJ-123 status to Done')\n\n"
            "What would you like to do?"
        )
        return state
    
    similar_tickets = state.get("similar_tickets", [])
    
    if similar_tickets:
        response_parts = [
            f"I found {len(similar_tickets)} similar ticket(s):\n"
        ]
        
        for i, ticket in enumerate(similar_tickets, 1):
            score = ticket.get("similarity_score", 0)
            desc = ticket.get("description", "")
            desc_preview = desc[:150] + "..." if len(desc) > 150 else desc
            response_parts.append(
                f"\n{i}. **{ticket['key']}** - {ticket['summary']}\n"
                f"   Status: {ticket['status']} | Priority: {ticket['priority']}\n"
                f"   Similarity: {score:.1%}\n"
                f"   Description: {desc_preview}\n"
            )
        
        response_parts.append(
            "\n\n**What would you like to do?**\n"
            "- Say 'create new ticket' or 'create a ticket' to add a new one\n"
            "- Say 'update [ticket-key]' to modify an existing ticket"
        )
        
        state["final_response"] = "".join(response_parts)
    else:
        state["final_response"] = (
            "I didn't find any similar tickets. "
            "Would you like me to create a new ticket for this issue? "
            "Just say 'create ticket' or 'create new ticket'."
        )
    
    return state


def should_continue_after_guardrail(state: AgentState) -> Literal["orchestrator", "end"]:
    """Route after guardrail: pass to orchestrator or end with rejection."""
    if state["is_valid_request"]:
        return "orchestrator"
    return "end"


def route_from_orchestrator(state: AgentState) -> Literal["similarity", "jira", "final", "end"]:
    """
    Route based on orchestrator's route_to decision.
    """
    route_to = state.get("route_to", "similarity")
    
    if route_to == "jira":
        return "jira"
    elif route_to == "similarity":
        return "similarity"
    else:
        return "final"


def should_create_ticket_after_similarity(state: AgentState) -> Literal["jira", "final"]:
    """
    After similarity: either create ticket (if intent=create and no duplicates)
    or show results to user for decision.
    """
    intent = state.get("intent", "search")
    
    if intent == "create":
        similar_tickets = state.get("similar_tickets", [])
        has_duplicate = any(
            ticket.get("similarity_score", 0) > 0.9
            for ticket in similar_tickets
        )
        if has_duplicate:
            logger.info("Found highly similar ticket, showing to user for decision")
            return "final"
        return "jira"
    
    # For search/verify - show results to user
    return "final"


def create_jira_graph() -> StateGraph:
    """
    Create the LangGraph workflow:
    Guardrail -> Orchestrator -> [Similarity | Jira | Final] -> End
    """
    workflow = StateGraph(AgentState)
    
    workflow.add_node("guardrail", guardrail_node)
    workflow.add_node("orchestrator", orchestrator_node)
    workflow.add_node("similarity", similarity_node)
    workflow.add_node("jira", jira_node)
    workflow.add_node("final", create_final_response_node)
    
    workflow.set_entry_point("guardrail")
    
    workflow.add_conditional_edges(
        "guardrail",
        should_continue_after_guardrail,
        {"orchestrator": "orchestrator", "end": END}
    )
    
    workflow.add_conditional_edges(
        "orchestrator",
        route_from_orchestrator,
        {
            "similarity": "similarity",
            "jira": "jira",
            "final": "final",
            "end": END
        }
    )
    
    workflow.add_conditional_edges(
        "similarity",
        should_create_ticket_after_similarity,
        {"jira": "jira", "final": "final"}
    )
    
    workflow.add_edge("jira", END)
    workflow.add_edge("final", END)
    
    graph = workflow.compile()
    logger.info("Jira graph compiled successfully")
    return graph


async def run_jira_assistant(user_query: str, conversation_id: str = None) -> dict:
    """
    Run the Jira assistant workflow.
    
    Flow:
    1. Guardrail validates + stores session_id
    2. Orchestrator routes: similarity (check/verify/first) or jira (create/update)
    3. Similarity checks historical data, searches, returns to UI for user decision
    4. Next turn: User says create/update -> Jira agent
    """
    logger.info(f"Processing query: {user_query}")
    
    initial_state: AgentState = {
        "user_query": user_query,
        "intent": None,
        "is_valid_request": True,
        "guardrail_message": None,
        "session_exists": False,
        "is_first_turn": True,
        "route_to": None,
        "similar_tickets": [],
        "has_similar_tickets": False,
        "has_historical_data": None,
        "action_type": None,
        "ticket_data": None,
        "created_ticket": None,
        "final_response": "",
        "timestamp": datetime.utcnow().isoformat(),
        "conversation_id": conversation_id,
        "error": None
    }
    
    graph = create_jira_graph()
    
    try:
        final_state = await graph.ainvoke(initial_state)
        
        return {
            "response": final_state.get("final_response", "I'm sorry, I couldn't process your request."),
            "intent": final_state.get("intent"),
            "similar_tickets": final_state.get("similar_tickets", []),
            "created_ticket": final_state.get("created_ticket"),
            "action_type": final_state.get("action_type"),
            "error": final_state.get("error"),
            "timestamp": final_state.get("timestamp"),
            "session_id": conversation_id,
        }
        
    except Exception as e:
        logger.error(f"Error running Jira assistant: {e}")
        return {
            "response": f"I encountered an error: {str(e)}",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
