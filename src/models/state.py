"""State definitions for the multi-agent system"""

from typing import TypedDict, List, Dict, Any, Optional
from datetime import datetime
from langchain_core.messages import BaseMessage


class JiraTicket(TypedDict):
    """Jira ticket data structure"""
    id: Optional[str]  # Internal Jira ID (e.g., "10003")
    key: str  # Human-readable key (e.g., "SCRUM-4")
    summary: str
    description: str
    status: str
    priority: str
    assignee: Optional[str]
    created: str
    updated: str
    issue_type: str
    labels: List[str]
    similarity_score: Optional[float]


class AgentState(TypedDict):
    """State shared across agents in the workflow"""
    
    # User input
    user_query: str
    
    # Conversation memory
    messages: List[BaseMessage]  # Chat history for memory
    
    # Intent classification
    intent: Optional[str]  # "search", "create", "update", "invalid"
    
    # Guardrail results
    is_valid_request: bool
    guardrail_message: Optional[str]
    
    # Similarity search results
    similar_tickets: List[JiraTicket]
    has_similar_tickets: bool
    
    # Jira operations
    action_type: Optional[str]  # "create", "update", "none"
    ticket_data: Optional[Dict[str, Any]]
    created_ticket: Optional[JiraTicket]
    
    # Response
    final_response: str
    
    # Metadata
    timestamp: str
    conversation_id: Optional[str]
    error: Optional[str]

