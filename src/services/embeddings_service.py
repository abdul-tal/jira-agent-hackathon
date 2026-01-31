"""Embeddings service for generating vector representations"""

from typing import List
from sentence_transformers import SentenceTransformer
from loguru import logger

from src.config import settings


class EmbeddingsService:
    """Service for generating embeddings from text"""
    
    def __init__(self):
        """Initialize embedding model"""
        # Using sentence-transformers for efficient local embeddings
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        logger.info("Embeddings service initialized with all-MiniLM-L6-v2")
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text
        
        Args:
            text: Input text
        
        Returns:
            List of floats representing the embedding
        """
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts
        
        Args:
            texts: List of input texts
        
        Returns:
            List of embeddings
        """
        embeddings = self.model.encode(texts, convert_to_numpy=True, show_progress_bar=True)
        return embeddings.tolist()
    
    def ticket_to_text(self, ticket: dict) -> str:
        """
        Convert ticket to searchable text
        
        Args:
            ticket: Ticket dictionary
        
        Returns:
            Combined text for embedding
        """
        parts = [
            f"Summary: {ticket.get('summary', '')}",
            f"Description: {ticket.get('description', '')}",
            f"Type: {ticket.get('issue_type', '')}",
            f"Priority: {ticket.get('priority', '')}",
            f"Status: {ticket.get('status', '')}",
            f"Labels: {', '.join(ticket.get('labels', []))}"
        ]
        return " | ".join(parts)

