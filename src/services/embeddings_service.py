"""Embeddings service for generating vector representations using OpenAI"""

from typing import List
from langchain_openai import OpenAIEmbeddings
from loguru import logger

from src.config import settings


class EmbeddingsService:
    """Service for generating embeddings from text using OpenAI"""
    
    def __init__(self):
        """
        Initialize OpenAI embedding model
        
        Note: Chunking is NOT used for Jira tickets because:
        - Tickets are naturally small (200-3000 characters typical)
        - Well below OpenAI limit (8191 tokens = ~32,000 characters)
        - Each ticket is already focused on one issue
        - Chunking would add unnecessary cost and complexity
        """
        # Initialize OpenAI embeddings
        # Using text-embedding-3-small (1536 dimensions, cost-effective)
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            openai_api_key=settings.openai_api_key
        )
        
        self.embedding_dimension = 1536  # Dimension for text-embedding-3-small
        
        logger.info(
            f"Embeddings service initialized with OpenAI text-embedding-3-small "
            f"(dim={self.embedding_dimension}, no chunking - tickets are small enough)"
        )
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text using OpenAI
        
        Args:
            text: Input text
        
        Returns:
            List of floats representing the embedding
        """
        try:
            embedding = self.embeddings.embed_query(text)
            return embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts using OpenAI batch API
        
        Args:
            texts: List of input texts (one per ticket)
        
        Returns:
            List of embeddings (one per ticket)
        """
        try:
            logger.info(f"Generating embeddings for {len(texts)} tickets...")
            embeddings = self.embeddings.embed_documents(texts)
            logger.info(f"Successfully generated {len(embeddings)} embeddings")
            return embeddings
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            raise
    
    def ticket_to_text(self, ticket: dict) -> str:
        """
        Convert ticket to searchable text for embedding
        
        Args:
            ticket: Ticket dictionary
        
        Returns:
            Combined text for embedding (no chunking - tickets are small enough)
        """
        parts = []
        
        # Add ID if available (internal Jira ID)
        if ticket.get('id'):
            parts.append(f"ID: {ticket.get('id')}")
        
        # Add key (human-readable identifier like SCRUM-4)
        parts.extend([
            f"Key: {ticket.get('key', '')}",
            f"Summary: {ticket.get('summary', '')}",
            f"Description: {ticket.get('description', '')}",
            f"Type: {ticket.get('issue_type', '')}",
            f"Priority: {ticket.get('priority', '')}",
            f"Status: {ticket.get('status', '')}",
            f"Labels: {', '.join(ticket.get('labels', []))}"
        ])
        
        return " | ".join(parts)
