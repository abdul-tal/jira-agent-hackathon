"""LangGraph workflow for Jira assistance"""

from datetime import datetime
from typing import Literal
from langgraph.graph import StateGraph, END
from loguru import logger

from src.models import AgentState
from src.agents import orchestrator_node, guardrail_node, similarity_node, jira_node


def create_final_response_node(state: AgentState) -> AgentState:
    """
    Create final response for search or info intents
    
    Args:
        state: Current agent state
    
    Returns:
        Updated state with final response
    """
    logger.info("Creating final response")
    
    intent = state.get("intent", "info")
    
    if intent == "search":
        similar_tickets = state.get("similar_tickets", [])
        
        if similar_tickets:
            response_parts = [
                f"I found {len(similar_tickets)} similar ticket(s):\n"
            ]
            
            for i, ticket in enumerate(similar_tickets, 1):
                score = ticket.get("similarity_score", 0)
                response_parts.append(
                    f"\n{i}. **{ticket['key']}** - {ticket['summary']}\n"
                    f"   Status: {ticket['status']} | Priority: {ticket['priority']}\n"
                    f"   Similarity: {score:.1%}\n"
                    f"   Description: {ticket['description'][:150]}..."
                )
            
            response_parts.append(
                "\n\nWould you like me to create a new ticket or update one of these?"
            )
            
            state["final_response"] = "".join(response_parts)
        else:
            state["final_response"] = (
                "I didn't find any similar tickets. "
                "Would you like me to create a new ticket for this issue?"
            )
    
    elif intent == "info":
        state["final_response"] = (
            "I'm your Jira assistant! I can help you:\n"
            "- Search for existing tickets\n"
            "- Create new tickets\n"
            "- Update existing tickets\n\n"
            "What would you like to do?"
        )
    
    return state


def should_continue_after_guardrail(state: AgentState) -> Literal["orchestrator", "end"]:
    """
    Route after guardrail check
    
    Args:
        state: Current agent state
    
    Returns:
        Next node to execute
    """
    if state["is_valid_request"]:
        return "orchestrator"
    else:
        return "end"


def should_check_similarity(state: AgentState) -> Literal["similarity", "jira", "final", "end"]:
    """
    Route after intent classification
    
    Args:
        state: Current agent state
    
    Returns:
        Next node to execute
    """
    intent = state.get("intent", "info")
    
    if intent == "create":
        # Check for similar tickets before creating
        return "similarity"
    elif intent == "update":
        # Go directly to Jira agent for updates
        return "jira"
    elif intent == "search":
        # Go to similarity search
        return "similarity"
    else:  # info or unknown
        return "final"


def should_create_ticket(state: AgentState) -> Literal["jira", "final"]:
    """
    Decide whether to create ticket after similarity search
    
    Args:
        state: Current agent state
    
    Returns:
        Next node to execute
    """
    intent = state.get("intent", "search")
    
    # If intent was create and no highly similar tickets found, create the ticket
    if intent == "create":
        similar_tickets = state.get("similar_tickets", [])
        
        # Check if any tickets are very similar (>90% similarity)
        has_duplicate = any(
            ticket.get("similarity_score", 0) > 0.9
            for ticket in similar_tickets
        )
        
        if has_duplicate:
            # Show similar tickets instead of creating
            logger.info("Found highly similar ticket, not creating new one")
            return "final"
        else:
            # Proceed with creation
            return "jira"
    else:
        # For search intent, just show results
        return "final"


def create_jira_graph() -> StateGraph:
    """
    Create the LangGraph workflow for Jira assistance
    
    Returns:
        Compiled StateGraph
    """
    # Create graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("guardrail", guardrail_node)
    workflow.add_node("orchestrator", orchestrator_node)
    workflow.add_node("similarity", similarity_node)
    workflow.add_node("jira", jira_node)
    workflow.add_node("final", create_final_response_node)
    
    # Set entry point
    workflow.set_entry_point("guardrail")
    
    # Add edges
    workflow.add_conditional_edges(
        "guardrail",
        should_continue_after_guardrail,
        {
            "orchestrator": "orchestrator",
            "end": END
        }
    )
    
    workflow.add_conditional_edges(
        "orchestrator",
        should_check_similarity,
        {
            "similarity": "similarity",
            "jira": "jira",
            "final": "final",
            "end": END
        }
    )
    
    workflow.add_conditional_edges(
        "similarity",
        should_create_ticket,
        {
            "jira": "jira",
            "final": "final"
        }
    )
    
    workflow.add_edge("jira", END)
    workflow.add_edge("final", END)
    
    # Compile
    graph = workflow.compile()
    
    logger.info("Jira graph compiled successfully")
    return graph


async def run_jira_assistant(user_query: str, conversation_id: str = None) -> dict:
    """
    Run the Jira assistant workflow
    
    Args:
        user_query: User's query/request
        conversation_id: Optional conversation ID
    
    Returns:
        Dictionary with response and metadata
    """
    logger.info(f"Processing query: {user_query}")
    
    # Initialize state
    initial_state: AgentState = {
        "user_query": user_query,
        "intent": None,
        "is_valid_request": True,
        "guardrail_message": None,
        "similar_tickets": [],
        "has_similar_tickets": False,
        "action_type": None,
        "ticket_data": None,
        "created_ticket": None,
        "final_response": "",
        "timestamp": datetime.utcnow().isoformat(),
        "conversation_id": conversation_id,
        "error": None
    }
    
    # Create and run graph
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
            "timestamp": final_state.get("timestamp")
        }
        
    except Exception as e:
        logger.error(f"Error running Jira assistant: {e}")
        return {
            "response": f"I encountered an error: {str(e)}",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

