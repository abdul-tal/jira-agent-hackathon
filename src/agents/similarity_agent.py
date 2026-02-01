"""Similarity agent for searching similar tickets"""

import sys
import os
from loguru import logger

from src.models import AgentState
from src.config import settings

# Add similarity_agent to path
similarity_agent_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    'similarity_agent'
)
sys.path.insert(0, similarity_agent_path)

from similarity_agent import SimilarityAgent


# Initialize similarity agent once (singleton pattern)
_similarity_agent = None


def get_similarity_agent() -> SimilarityAgent:
    """Get or create the similarity agent instance"""
    global _similarity_agent
    if _similarity_agent is None:
        _similarity_agent = SimilarityAgent()
    return _similarity_agent


async def similarity_node(state: AgentState, config: dict = None) -> AgentState:
    """
    Search for similar tickets using the dedicated similarity agent
    
    Args:
        state: Current agent state
        config: LangGraph config containing runtime context
    
    Returns:
        Updated state with similar tickets
    """
    logger.info("Similarity agent: Searching for similar tickets")
    
    # Emit event if queue is available
    event_queue = config.get("configurable", {}).get("event_queue") if config else None
    if event_queue:
        await event_queue.put({'event': 'similarity', 'message': '🔍 Searching for similar tickets...'})
    
    query = state["user_query"]
    max_results = getattr(settings, 'max_similarity_results', 5)
    
    try:
        # Use the similarity agent to search
        agent = get_similarity_agent()
        result = agent.search(query=query, max_results=max_results)
        
        # Map the similarity agent response to our state format
        matched_tickets = result.get("matched_tickets", [])
        
        if matched_tickets:
            # Convert to our JiraTicket format
            similar_tickets = []
            for ticket in matched_tickets:
                similar_ticket = {
                    "key": ticket.get("key", ""),
                    "summary": ticket.get("summary", ""),
                    "description": ticket.get("description", ""),
                    "status": ticket.get("status", ""),
                    "priority": ticket.get("priority", ""),
                    "issue_type": ticket.get("issue_type", ""),
                    "labels": ticket.get("labels", []),
                    "similarity_score": ticket.get("similarity_score", 0.0),
                    "id": None,
                    "assignee": None,
                    "created": "",
                    "updated": ""
                }
                similar_tickets.append(similar_ticket)
            
            state["similar_tickets"] = similar_tickets
            state["has_similar_tickets"] = True
            
            logger.info(
                f"Found {len(similar_tickets)} similar tickets "
                f"(confidence: {result.get('confidence_level', 'unknown')})"
            )
            
            # Emit success event
            if event_queue:
                count = len(similar_tickets)
                await event_queue.put({
                    'event': 'similarity_found',
                    'message': f'✅ Found {count} similar ticket{"s" if count != 1 else ""}!',
                    'count': count
                })
        else:
            state["similar_tickets"] = []
            state["has_similar_tickets"] = False
            logger.info("No similar tickets found")
            
            # Emit no results event
            if event_queue:
                await event_queue.put({'event': 'similarity_not_found', 'message': '📝 No similar tickets found'})
        
        # Store additional metadata if needed
        if result.get("error"):
            state["error"] = result["error"]
        
    except Exception as e:
        logger.error(f"Similarity agent error: {e}")
        state["similar_tickets"] = []
        state["has_similar_tickets"] = False
        state["error"] = str(e)
    
    return state

