"""Vector search tools for similarity matching"""

from typing import List
from langchain.tools import tool
from loguru import logger

from src.services import VectorStore, EmbeddingsService
from src.config import settings


# Global service instances
_vector_store = None
_embeddings_service = None


def get_vector_store() -> VectorStore:
    """Get or create vector store instance"""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store


def get_embeddings_service() -> EmbeddingsService:
    """Get or create embeddings service instance"""
    global _embeddings_service
    if _embeddings_service is None:
        _embeddings_service = EmbeddingsService()
    return _embeddings_service


@tool
def search_similar_tickets_tool(query: str, max_results: int = 5) -> dict:
    """
    Search for similar Jira tickets based on the query.
    
    This tool uses semantic search to find tickets that are similar to the given query.
    It's useful for checking if a similar ticket already exists before creating a new one.
    
    Args:
        query: The search query describing what to look for
        max_results: Maximum number of similar tickets to return (default: 5)
    
    Returns:
        Dictionary containing similar tickets and their similarity scores
    """
    try:
        vector_store = get_vector_store()
        embeddings_service = get_embeddings_service()
        
        # Generate embedding for query
        query_embedding = embeddings_service.generate_embedding(query)
        
        # Search for similar tickets
        results = vector_store.search(
            query_embedding=query_embedding,
            k=max_results,
            threshold=settings.similarity_threshold
        )
        
        if not results:
            return {
                "success": True,
                "similar_tickets": [],
                "count": 0,
                "message": "No similar tickets found"
            }
        
        # Format results
        similar_tickets = []
        for ticket, score in results:
            similar_tickets.append({
                "key": ticket["key"],
                "summary": ticket["summary"],
                "description": ticket["description"][:200] + "..." if len(ticket["description"]) > 200 else ticket["description"],
                "status": ticket["status"],
                "priority": ticket["priority"],
                "similarity_score": round(score, 3)
            })
        
        return {
            "success": True,
            "similar_tickets": similar_tickets,
            "count": len(similar_tickets),
            "message": f"Found {len(similar_tickets)} similar ticket(s)"
        }
        
    except Exception as e:
        logger.error(f"Error searching for similar tickets: {e}")
        return {
            "success": False,
            "error": str(e),
            "similar_tickets": [],
            "count": 0,
            "message": f"Failed to search for similar tickets: {str(e)}"
        }

