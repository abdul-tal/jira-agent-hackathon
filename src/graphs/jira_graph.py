"""LangGraph workflow for Jira assistance"""

import asyncio
from datetime import datetime
from typing import Literal
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, AIMessage
from loguru import logger

from src.models import AgentState
from src.agents import orchestrator_node, guardrail_node, similarity_node, jira_node


# Global memory saver for conversation persistence
memory = MemorySaver()


async def create_final_response_node(state: AgentState, config: dict = None) -> AgentState:
    """
    Create final response for search or info intents
    
    Args:
        state: Current agent state
        config: LangGraph config containing runtime context
    
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
    # If guardrail already set a response (greetings/help), go to end
    if state.get("final_response"):
        logger.info("Guardrail handled request directly, skipping to end")
        return "end"
    
    # If request is valid, continue to orchestrator
    if state["is_valid_request"]:
        return "orchestrator"
    else:
        # Invalid request, go to end
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
        # Go directly to Jira agent to create the ticket
        logger.info("Create intent - going directly to Jira agent")
        return "jira"
    elif intent == "update":
        # Go directly to Jira agent for updates
        return "jira"
    elif intent == "search":
        # Go to similarity search
        return "similarity"
    else:  # info or unknown
        return "final"




def create_jira_graph() -> StateGraph:
    """
    Create the LangGraph workflow for Jira assistance with memory
    
    Returns:
        Compiled StateGraph with checkpointing enabled
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
    
    # Similarity only goes to final (for search results)
    workflow.add_edge("similarity", "final")
    
    workflow.add_edge("jira", END)
    workflow.add_edge("final", END)
    
    # Compile with memory checkpointing
    graph = workflow.compile(checkpointer=memory)
    
    logger.info("Jira graph compiled successfully with memory enabled")
    return graph


def get_conversation_history(conversation_id: str) -> list:
    """
    Retrieve conversation history for a given conversation ID
    
    Args:
        conversation_id: The conversation/thread ID
    
    Returns:
        List of messages in the conversation
    """
    try:
        thread_id = conversation_id or "default"
        config = {"configurable": {"thread_id": thread_id}}
        
        # Get checkpoint from memory
        checkpoint = memory.get(config)
        if checkpoint and "messages" in checkpoint.get("channel_values", {}):
            return checkpoint["channel_values"]["messages"]
        return []
    except Exception as e:
        logger.error(f"Error retrieving conversation history: {e}")
        return []


async def run_jira_assistant(user_query: str, conversation_id: str = None, event_queue: 'asyncio.Queue' = None) -> dict:
    """
    Run the Jira assistant workflow with conversation memory
    
    Args:
        user_query: User's query/request
        conversation_id: Optional conversation ID (used as thread_id for memory)
        event_queue: Optional asyncio queue for streaming events
    
    Returns:
        Dictionary with response and metadata
    """
    logger.info(f"Processing query: {user_query} [conversation_id: {conversation_id}]")
    
    # Use conversation_id as thread_id, or create a default one
    thread_id = conversation_id or "default"
    
    # Initialize state with user message
    initial_state: AgentState = {
        "user_query": user_query,
        "messages": [HumanMessage(content=user_query)],
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
    
    # Create graph and configure with thread_id for memory
    graph = create_jira_graph()
    config = {
        "configurable": {
            "thread_id": thread_id,
            "event_queue": event_queue  # Pass event queue in config (not serialized)
        }
    }
    
    try:
        # Run graph with memory enabled
        final_state = await graph.ainvoke(initial_state, config)
        
        # Add assistant's response to messages
        response_message = final_state.get("final_response", "I'm sorry, I couldn't process your request.")
        
        # Log the response for debugging
        logger.info(f"Final response from graph: {response_message[:200]}")  # Log first 200 chars
        logger.info(f"Response type: {type(response_message)}")
        
        # Update messages with AI response for next conversation turn
        if "messages" in final_state:
            final_state["messages"].append(AIMessage(content=response_message))
        
        return {
            "response": response_message,
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

