"""FastAPI application for Jira Assistant"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from loguru import logger

from src.config import settings
from src.jobs import TicketSyncJob
from src.graphs import run_jira_assistant


# Global sync job instance
sync_job: Optional[TicketSyncJob] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events
    """
    global sync_job
    
    # Startup
    logger.info("Starting Jira Assistant API...")
    
    # Initialize and start sync job
    sync_job = TicketSyncJob()
    sync_job.start()
    
    logger.info("Jira Assistant API started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Jira Assistant API...")
    
    if sync_job:
        sync_job.stop()
    
    logger.info("Jira Assistant API shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Jira Assistant API",
    description="Multi-agent chatbot for Jira assistance",
    version="1.0.0",
    lifespan=lifespan
)


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response models
class ChatRequest(BaseModel):
    """Chat request model"""
    query: str
    conversation_id: Optional[str] = None


class TicketInfo(BaseModel):
    """Ticket information model"""
    key: str
    summary: str
    description: str
    status: str
    priority: str
    similarity_score: Optional[float] = None


class ChatResponse(BaseModel):
    """Chat response model"""
    response: str
    intent: Optional[str] = None
    similar_tickets: List[TicketInfo] = []
    created_ticket: Optional[TicketInfo] = None
    action_type: Optional[str] = None
    error: Optional[str] = None
    timestamp: str


class SyncResponse(BaseModel):
    """Sync response model"""
    message: str
    status: str


# API Routes
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Jira Assistant API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "jira-assistant"
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint for Jira assistance
    
    Args:
        request: Chat request with user query
    
    Returns:
        Chat response with assistant's reply
    """
    try:
        if not request.query or not request.query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        # Run the Jira assistant
        result = await run_jira_assistant(
            user_query=request.query,
            conversation_id=request.conversation_id
        )
        
        # Format similar tickets
        similar_tickets = [
            TicketInfo(**ticket)
            for ticket in result.get("similar_tickets", [])
        ]
        
        # Format created ticket
        created_ticket = None
        if result.get("created_ticket"):
            created_ticket = TicketInfo(**result["created_ticket"])
        
        return ChatResponse(
            response=result["response"],
            intent=result.get("intent"),
            similar_tickets=similar_tickets,
            created_ticket=created_ticket,
            action_type=result.get("action_type"),
            error=result.get("error"),
            timestamp=result["timestamp"]
        )
        
    except Exception as e:
        logger.error(f"Error processing chat request: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/sync", response_model=SyncResponse)
async def trigger_sync():
    """
    Manually trigger a ticket sync job
    
    Returns:
        Sync status
    """
    try:
        global sync_job
        
        if not sync_job:
            raise HTTPException(status_code=503, detail="Sync job not initialized")
        
        # Trigger sync in background
        import asyncio
        asyncio.create_task(sync_job.run_now())
        
        return SyncResponse(
            message="Ticket sync triggered successfully",
            status="running"
        )
        
    except Exception as e:
        logger.error(f"Error triggering sync: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats")
async def get_stats():
    """
    Get statistics about the vector store
    
    Returns:
        Statistics dictionary
    """
    try:
        from src.services import VectorStore
        
        vector_store = VectorStore()
        
        return {
            "total_tickets": vector_store.index.ntotal if vector_store.index else 0,
            "dimension": vector_store.dimension,
            "index_path": str(vector_store.index_path)
        }
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.api.main:app",
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower(),
        reload=False
    )

