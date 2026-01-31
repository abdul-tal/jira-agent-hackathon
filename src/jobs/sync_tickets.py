"""Background job for syncing Jira tickets to vector store"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from loguru import logger

from src.services import JiraService, VectorStore, EmbeddingsService
from src.config import settings


class TicketSyncJob:
    """Background job to sync Jira tickets to vector store"""
    
    def __init__(self):
        """Initialize sync job"""
        self.scheduler = AsyncIOScheduler()
        self.jira_service = JiraService()
        self.vector_store = VectorStore()
        self.embeddings_service = EmbeddingsService()
        
        logger.info("Ticket sync job initialized")
    
    async def sync_tickets(self):
        """
        Fetch all Jira tickets, generate embeddings, and update vector store
        
        Note: No chunking is used because Jira tickets are naturally small (200-3000 chars)
        and well below OpenAI's limit (8191 tokens = ~32,000 chars). Each ticket gets
        one embedding for simplicity, lower cost, and better performance.
        """
        try:
            logger.info("Starting ticket sync job...")
            
            # Fetch all tickets from Jira
            logger.info("Fetching tickets from Jira...")
            tickets = self.jira_service.fetch_all_tickets()
            
            if not tickets:
                logger.warning("No tickets found in Jira")
                return
            
            logger.info(f"Fetched {len(tickets)} tickets from Jira")
            
            # Convert tickets to searchable text (one text per ticket, no chunking)
            logger.info("Converting tickets to searchable text...")
            ticket_texts = [
                self.embeddings_service.ticket_to_text(ticket)
                for ticket in tickets
            ]
            
            # Generate embeddings (one embedding per ticket)
            logger.info(f"Generating OpenAI embeddings for {len(ticket_texts)} tickets...")
            embeddings = self.embeddings_service.generate_embeddings_batch(ticket_texts)
            
            logger.info(f"Generated {len(embeddings)} embeddings")
            
            # Rebuild vector store (simple 1:1 mapping - one ticket = one embedding)
            logger.info("Updating vector store...")
            self.vector_store.rebuild(tickets, embeddings)
            
            logger.info(
                f"✅ Ticket sync completed successfully! "
                f"Indexed {len(tickets)} tickets in vector store."
            )
            
        except Exception as e:
            logger.error(f"Error during ticket sync: {e}")
            raise
    
    def start(self):
        """
        Start the background scheduler
        """
        # Run sync on startup if configured
        if settings.sync_on_startup:
            logger.info("Running initial ticket sync on startup...")
            import asyncio
            asyncio.create_task(self.sync_tickets())
        
        # Schedule periodic sync
        trigger = IntervalTrigger(hours=settings.sync_interval_hours)
        self.scheduler.add_job(
            self.sync_tickets,
            trigger=trigger,
            id="sync_tickets",
            name="Sync Jira Tickets",
            replace_existing=True
        )
        
        self.scheduler.start()
        logger.info(
            f"Ticket sync job scheduled to run every {settings.sync_interval_hours} hours"
        )
    
    def stop(self):
        """
        Stop the background scheduler
        """
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Ticket sync job stopped")
    
    async def run_now(self):
        """
        Manually trigger a sync job (useful for API endpoints)
        """
        logger.info("Manual sync triggered")
        await self.sync_tickets()

