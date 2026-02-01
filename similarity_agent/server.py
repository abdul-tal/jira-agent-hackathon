"""FastAPI Server for Similarity Agent

Run this server to use the Similarity Agent as a standalone API service.

Usage:
    python -m similarity_agent.server

The server will start on http://localhost:8001
"""

import sys
from pathlib import Path
from typing import Optional
from datetime import datetime

# Add parent directory to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from loguru import logger

from similarity_agent import SimilarityAgent


# Initialize FastAPI app
app = FastAPI(
    title="Similarity Agent API",
    description="Search for similar Jira tickets using semantic search",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the agent (singleton)
agent: Optional[SimilarityAgent] = None


def get_agent() -> SimilarityAgent:
    """Get or create the similarity agent instance."""
    global agent
    if agent is None:
        logger.info("Initializing Similarity Agent...")
        agent = SimilarityAgent()
        logger.info("Similarity Agent ready")
    return agent


# Request/Response Models
class SearchRequest(BaseModel):
    """Request model for similarity search."""
    query: str = Field(..., description="User's search query", min_length=1, max_length=1000)
    max_results: int = Field(5, description="Maximum number of results to return", ge=1, le=20)
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "User login fails with 401 error",
                "max_results": 5
            }
        }


class MatchedTicket(BaseModel):
    """Model for a matched ticket."""
    key: str
    summary: str
    description: str
    issue_type: str
    priority: str
    status: str
    labels: list[str]
    similarity_score: float
    match_reason: Optional[str] = None


class SearchResponse(BaseModel):
    """Response model for similarity search."""
    matched_tickets: list[dict]
    message: str
    has_matches: bool
    total_matches: int
    confidence_level: str
    timestamp: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "matched_tickets": [
                    {
                        "key": "SCRUM-5",
                        "summary": "User authentication issue in login page",
                        "description": "Users unable to login...",
                        "issue_type": "Bug",
                        "priority": "High",
                        "status": "In Progress",
                        "labels": ["authentication", "login"],
                        "similarity_score": 0.87,
                        "match_reason": "Both describe login authentication failures"
                    }
                ],
                "message": "Found 1 highly relevant ticket matching your query.",
                "has_matches": True,
                "total_matches": 1,
                "confidence_level": "high",
                "timestamp": "2026-02-01T10:30:00.000Z"
            }
        }


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    agent_ready: bool
    timestamp: str


# API Endpoints
@app.get("/", tags=["Info"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Similarity Agent API",
        "version": "1.0.0",
        "description": "Search for similar Jira tickets using semantic search",
        "endpoints": {
            "search": "/search",
            "health": "/health",
            "docs": "/docs"
        }
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint."""
    try:
        agent_instance = get_agent()
        agent_ready = agent_instance is not None
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        agent_ready = False
    
    return {
        "status": "healthy" if agent_ready else "unhealthy",
        "agent_ready": agent_ready,
        "timestamp": datetime.now().isoformat()
    }


@app.post("/search", response_model=SearchResponse, tags=["Search"])
async def search_similar_tickets(request: SearchRequest):
    """
    Search for similar Jira tickets based on a query.
    
    This endpoint uses semantic search to find existing tickets that match
    the user's query. It returns matched tickets with full details and a
    human-readable message explaining the results.
    
    Args:
        request: SearchRequest containing query and max_results
    
    Returns:
        SearchResponse with matched_tickets and message
    
    Example:
        POST /search
        {
            "query": "User login fails with 401 error",
            "max_results": 5
        }
        
        Response:
        {
            "matched_tickets": [...],
            "message": "Found 2 highly relevant tickets...",
            "has_matches": true,
            "total_matches": 2,
            "confidence_level": "high",
            "timestamp": "2026-02-01T10:30:00.000Z"
        }
    """
    try:
        logger.info(f"Search request: query='{request.query}', max_results={request.max_results}")
        
        # Get the agent
        agent_instance = get_agent()
        
        # Perform search
        result = agent_instance.search(
            query=request.query,
            max_results=request.max_results
        )
        
        logger.info(
            f"Search complete: found {result['total_matches']} matches, "
            f"confidence={result['confidence_level']}"
        )
        
        # Return response in the required format
        return SearchResponse(
            matched_tickets=result["matched_tickets"],
            message=result["message"],
            has_matches=result["has_matches"],
            total_matches=result["total_matches"],
            confidence_level=result["confidence_level"],
            timestamp=result["timestamp"]
        )
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )


@app.get("/graph", tags=["Info"])
async def get_graph_structure():
    """Get the agent's graph structure."""
    try:
        agent_instance = get_agent()
        return {
            "graph": agent_instance.get_graph_visualization()
        }
    except Exception as e:
        logger.error(f"Failed to get graph structure: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get graph structure: {str(e)}"
        )


# Startup/Shutdown Events
@app.on_event("startup")
async def startup_event():
    """Initialize the agent on startup."""
    logger.info("="*80)
    logger.info("Starting Similarity Agent API Server")
    logger.info("="*80)
    
    try:
        # Initialize agent
        get_agent()
        logger.info("✓ Similarity Agent initialized successfully")
        logger.info("✓ Server ready to accept requests")
        logger.info("="*80)
    except Exception as e:
        logger.error(f"✗ Failed to initialize agent: {e}")
        logger.error("Server may not function correctly")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down Similarity Agent API Server")


# Main entry point
if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting Similarity Agent Server...")
    logger.info("Server will be available at: http://localhost:8001")
    logger.info("API documentation at: http://localhost:8001/docs")
    logger.info("Press Ctrl+C to stop")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        log_level="info"
    )

