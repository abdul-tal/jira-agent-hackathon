"""FastAPI application for Jira Assistant"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, AsyncGenerator, Dict, Any
from loguru import logger
import json
import asyncio
from datetime import datetime

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
    session_id: str
    question: str


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
    session_id: str
    message: str
    tickets: List[TicketInfo] = []
    type: str  # SIMILAR, CREATED, or UPDATED
    error: Optional[str] = None


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
        request: Chat request with session_id and question
    
    Returns:
        Chat response with assistant's reply
    """
    try:
        if not request.question or not request.question.strip():
            raise HTTPException(status_code=400, detail="Question cannot be empty")
        
        # Run the Jira assistant
        result = await run_jira_assistant(
            user_query=request.question,
            conversation_id=request.session_id
        )
        
        # Determine response type based on workflow execution
        tickets = []
        intent = result.get("intent", "search")
        
        if intent == "search" or result.get("similar_tickets"):
            # Similarity agent was called - return similar tickets (user decides next action)
            response_type = "SIMILAR"
            if result.get("similar_tickets"):
                for ticket in result["similar_tickets"]:
                    try:
                        tickets.append(TicketInfo(**ticket))
                    except Exception:
                        tickets.append(TicketInfo(
                            key=ticket.get("key", ""),
                            summary=ticket.get("summary", ""),
                            description=ticket.get("description", ""),
                            status=ticket.get("status", ""),
                            priority=ticket.get("priority", ""),
                            similarity_score=ticket.get("similarity_score")
                        ))
        
        elif intent == "create":
            # Jira agent created a new ticket
            response_type = "CREATED"
            if result.get("created_ticket"):
                ct = result["created_ticket"]
                try:
                    tickets = [TicketInfo(**ct)]
                except Exception:
                    tickets = [TicketInfo(
                        key=ct.get("key", ""),
                        summary=ct.get("summary", ""),
                        description=ct.get("description", ""),
                        status=ct.get("status", ""),
                        priority=ct.get("priority", ""),
                        similarity_score=ct.get("similarity_score")
                    )]
        
        elif intent == "update":
            # Jira agent updated an existing ticket
            response_type = "UPDATED"
            if result.get("created_ticket"):
                ct = result["created_ticket"]
                try:
                    tickets = [TicketInfo(**ct)]
                except Exception:
                    tickets = [TicketInfo(
                        key=ct.get("key", ""),
                        summary=ct.get("summary", ""),
                        description=ct.get("description", ""),
                        status=ct.get("status", ""),
                        priority=ct.get("priority", ""),
                        similarity_score=ct.get("similarity_score")
                    )]
        
        else:
            # Fallback (info/help)
            response_type = "SIMILAR"
            if result.get("similar_tickets"):
                for ticket in result["similar_tickets"]:
                    try:
                        tickets.append(TicketInfo(**ticket))
                    except Exception:
                        pass
        
        return ChatResponse(
            session_id=request.session_id,
            message=result["response"],
            tickets=tickets,
            type=response_type,
            error=result.get("error")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing chat request: {e}")
        return ChatResponse(
            session_id=request.session_id,
            message="",
            tickets=[],
            type="SIMILAR",
            error=str(e)
        )


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Streaming chat endpoint that sends real-time events
    
    Args:
        request: Chat request with session_id and question
    
    Returns:
        Server-Sent Events stream with progress updates
    """
    async def event_generator() -> AsyncGenerator[str, None]:
        """Generate Server-Sent Events"""
        try:
            if not request.question or not request.question.strip():
                yield f"data: {json.dumps({'event': 'error', 'message': 'Question cannot be empty'})}\n\n"
                return
            
            # Send initial event
            yield f"data: {json.dumps({'event': 'start', 'message': 'Processing your request...', 'timestamp': datetime.now().isoformat()})}\n\n"
            await asyncio.sleep(0.1)
            
            # Create a queue for events from the graph
            event_queue = asyncio.Queue()
            
            # Run assistant with event streaming
            async def run_with_events():
                """Run assistant and collect events"""
                try:
                    # Guardrail check
                    await event_queue.put({'event': 'guardrail', 'message': '🛡️  Validating request...'})
                    await asyncio.sleep(0.3)
                    
                    # Orchestrator
                    await event_queue.put({'event': 'orchestrator', 'message': '🧠 Analyzing intent...'})
                    await asyncio.sleep(0.3)
                    
                    # Similarity search
                    await event_queue.put({'event': 'similarity', 'message': '🔍 Searching for similar tickets...'})
                    
                    # Run the actual assistant
                    result = await run_jira_assistant(
                        user_query=request.question,
                        conversation_id=request.session_id
                    )
                    
                    # Send results based on what actually happened
                    intent = result.get("intent", "search")
                    
                    if intent == "search":
                        # Similarity search was performed
                        if result.get("similar_tickets"):
                            count = len(result["similar_tickets"])
                            await event_queue.put({
                                'event': 'similarity_found',
                                'message': f'✅ Found {count} similar ticket{"s" if count != 1 else ""}!',
                                'count': count
                            })
                        else:
                            await event_queue.put({'event': 'similarity_not_found', 'message': '📝 No similar tickets found'})
                    
                    elif intent == "create":
                        # New ticket was created
                        if result.get("created_ticket"):
                            await event_queue.put({
                                'event': 'ticket_created',
                                'message': f'🎉 Created ticket {result["created_ticket"]["key"]}!',
                                'ticket_key': result["created_ticket"]["key"]
                            })
                    
                    elif intent == "update":
                        # Existing ticket was updated
                        if result.get("created_ticket"):
                            await event_queue.put({
                                'event': 'ticket_updated',
                                'message': f'✨ Updated ticket {result["created_ticket"]["key"]}!',
                                'ticket_key': result["created_ticket"]["key"]
                            })
                    
                    # Transform result to match new response schema
                    tickets = []
                    intent = result.get("intent", "search")
                    
                    if intent == "search":
                        # Similarity agent was called - return similar tickets
                        response_type = "SIMILAR"
                        if result.get("similar_tickets"):
                            tickets = result["similar_tickets"]
                    
                    elif intent == "create":
                        # Jira agent was called to create a new ticket
                        response_type = "CREATED"
                        if result.get("created_ticket"):
                            tickets = [result["created_ticket"]]
                    
                    elif intent == "update":
                        # Jira agent was called to update an existing ticket
                        response_type = "UPDATED"
                        if result.get("created_ticket"):
                            # For updates, created_ticket contains the updated ticket info
                            tickets = [result["created_ticket"]]
                    
                    else:
                        # Fallback to SIMILAR for unknown intents
                        response_type = "SIMILAR"
                        if result.get("similar_tickets"):
                            tickets = result["similar_tickets"]
                    
                    formatted_result = {
                        'session_id': request.session_id,
                        'message': result.get('response', ''),
                        'tickets': tickets,
                        'type': response_type,
                        'error': result.get('error')
                    }
                    
                    # Send final result
                    await event_queue.put({'event': 'complete', 'result': formatted_result})
                    
                except Exception as e:
                    logger.error(f"Error in event generator: {e}")
                    await event_queue.put({'event': 'error', 'message': str(e)})
                finally:
                    await event_queue.put({'event': 'done'})
            
            # Start the assistant in background
            task = asyncio.create_task(run_with_events())
            
            # Stream events as they come
            while True:
                try:
                    event = await asyncio.wait_for(event_queue.get(), timeout=60.0)
                    
                    if event['event'] == 'done':
                        break
                    
                    event['timestamp'] = datetime.now().isoformat()
                    yield f"data: {json.dumps(event)}\n\n"
                    await asyncio.sleep(0.05)  # Small delay for smooth streaming
                    
                except asyncio.TimeoutError:
                    yield f"data: {json.dumps({'event': 'error', 'message': 'Request timeout'})}\n\n"
                    break
            
            # Wait for task to complete
            await task
            
        except Exception as e:
            logger.error(f"Error in event stream: {e}")
            yield f"data: {json.dumps({'event': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


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

