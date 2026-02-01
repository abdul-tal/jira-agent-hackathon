"""State definitions for the Similarity Agent"""

from typing import TypedDict, List, Dict, Any, Optional
from datetime import datetime


class MatchedTicket(TypedDict):
    """Matched Jira ticket with similarity information"""
    key: str
    summary: str
    description: str
    issue_type: str
    priority: str
    status: str
    labels: List[str]
    similarity_score: float
    match_reason: Optional[str]  # Why this ticket matched


class SimilarityAgentState(TypedDict):
    """State for the Similarity Agent graph"""
    
    # Input
    user_query: str
    max_results: int  # Maximum number of results to return
    
    # Query Analysis
    query_analysis: Optional[Dict[str, Any]]  # Parsed query components
    search_keywords: Optional[List[str]]  # Extracted keywords for search
    
    # Search Results
    matched_tickets: List[MatchedTicket]  # Tickets found
    total_matches: int  # Total number of matches
    best_match: Optional[MatchedTicket]  # Highest scoring match
    
    # Response
    has_matches: bool
    response_message: str  # Human-readable response
    confidence_level: str  # "high", "medium", "low"
    
    # Metadata
    timestamp: str
    error: Optional[str]

