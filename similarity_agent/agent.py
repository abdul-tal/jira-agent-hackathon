"""Similarity Agent - Main LangGraph implementation

This agent finds existing Jira tickets similar to a user's query using semantic search.
It analyzes the query, searches the vector store, and provides intelligent recommendations.
"""

from typing import Dict, Any
from datetime import datetime
from loguru import logger

from langgraph.graph import StateGraph, END
from similarity_agent.state import SimilarityAgentState
from similarity_agent.nodes import (
    analyze_query_node,
    search_tickets_node,
    analyze_results_node,
    format_response_node
)


class SimilarityAgent:
    """
    LangGraph-based agent for finding similar Jira tickets.
    
    This agent uses a multi-node workflow to:
    1. Analyze the user's query
    2. Search the vector store for similar tickets
    3. Analyze and rank the results
    4. Generate a comprehensive response
    
    Example:
        >>> agent = SimilarityAgent()
        >>> result = agent.search("User login is failing with 401 error")
        >>> print(result["response_message"])
        >>> for ticket in result["matched_tickets"]:
        ...     print(f"{ticket['key']}: {ticket['summary']}")
    """
    
    def __init__(self):
        """Initialize the similarity agent with the LangGraph workflow."""
        self.graph = self._build_graph()
        logger.info("Similarity Agent initialized")
    
    def _build_graph(self) -> StateGraph:
        """
        Build the LangGraph workflow for similarity search.
        
        Graph Structure:
            START
              ↓
          analyze_query ← Understand what user is looking for
              ↓
          search_tickets ← Find similar tickets in vector store
              ↓
          analyze_results ← Evaluate matches and confidence
              ↓
          format_response ← Create comprehensive response
              ↓
            END
        
        Returns:
            Compiled StateGraph ready for execution
        """
        workflow = StateGraph(SimilarityAgentState)
        
        # Add nodes
        workflow.add_node("analyze_query", analyze_query_node)
        workflow.add_node("search_tickets", search_tickets_node)
        workflow.add_node("analyze_results", analyze_results_node)
        workflow.add_node("format_response", format_response_node)
        
        # Define the flow
        workflow.set_entry_point("analyze_query")
        workflow.add_edge("analyze_query", "search_tickets")
        workflow.add_edge("search_tickets", "analyze_results")
        workflow.add_edge("analyze_results", "format_response")
        workflow.add_edge("format_response", END)
        
        # Compile the graph
        app = workflow.compile()
        
        logger.info("Similarity Agent graph compiled successfully")
        return app
    
    def search(
        self,
        query: str,
        max_results: int = 5
    ) -> Dict[str, Any]:
        """
        Search for similar Jira tickets based on a user query.
        
        Args:
            query: User's search query or problem description
            max_results: Maximum number of similar tickets to return (default: 5)
        
        Returns:
            Dictionary containing:
                - matched_tickets: List of matching tickets with full details
                - message: Human-readable message about the search results
                - has_matches: Whether any matches were found
                - total_matches: Number of matches found
                - confidence_level: "high", "medium", "low", or "none"
                - best_match: Highest scoring match
                - query_analysis: Parsed query components
                - timestamp: When the search was performed
        
        Example:
            >>> agent = SimilarityAgent()
            >>> result = agent.search("Login page shows 401 error")
            >>> print(result["message"])
            >>> for ticket in result["matched_tickets"]:
            ...     print(f"{ticket['key']}: {ticket['summary']}")
        """
        logger.info(f"Searching for similar tickets: '{query}'")
        
        # Initialize state
        initial_state: SimilarityAgentState = {
            "user_query": query,
            "max_results": max_results,
            "query_analysis": None,
            "search_keywords": None,
            "matched_tickets": [],
            "total_matches": 0,
            "best_match": None,
            "has_matches": False,
            "response_message": "",
            "confidence_level": "none",
            "timestamp": datetime.now().isoformat(),
            "error": None
        }
        
        try:
            # Execute the graph
            final_state = self.graph.invoke(initial_state)
            
            logger.info(
                f"Search complete: found {final_state['total_matches']} matches, "
                f"confidence={final_state['confidence_level']}"
            )
            
            # Return with clear structure: matched_tickets and message
            return {
                "matched_tickets": final_state["matched_tickets"],
                "message": final_state["response_message"],
                "has_matches": final_state["has_matches"],
                "total_matches": final_state["total_matches"],
                "confidence_level": final_state["confidence_level"],
                "best_match": final_state["best_match"],
                "query_analysis": final_state.get("query_analysis"),
                "timestamp": final_state["timestamp"],
                "error": final_state.get("error")
            }
            
        except Exception as e:
            logger.error(f"Error executing similarity search: {e}")
            return {
                "matched_tickets": [],
                "message": f"An error occurred while searching for similar tickets: {str(e)}",
                "has_matches": False,
                "total_matches": 0,
                "confidence_level": "none",
                "best_match": None,
                "query_analysis": None,
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
    
    def get_graph_visualization(self) -> str:
        """
        Get a text representation of the graph structure.
        
        Returns:
            String showing the graph nodes and edges
        """
        return """
Similarity Agent Graph:

    START
      ↓
  ┌─────────────────┐
  │ analyze_query   │ ← Parse user query and extract keywords
  └─────────────────┘
      ↓
  ┌─────────────────┐
  │ search_tickets  │ ← Search vector store for similar tickets
  └─────────────────┘
      ↓
  ┌─────────────────┐
  │ analyze_results │ ← Evaluate matches and confidence level
  └─────────────────┘
      ↓
  ┌─────────────────┐
  │ format_response │ ← Create comprehensive response
  └─────────────────┘
      ↓
    END
"""


def create_similarity_agent() -> SimilarityAgent:
    """
    Factory function to create a SimilarityAgent instance.
    
    Returns:
        Configured SimilarityAgent ready to use
    """
    return SimilarityAgent()

