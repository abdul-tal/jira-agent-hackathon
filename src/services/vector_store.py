"""Vector store service using FAISS"""

import pickle
from pathlib import Path
from typing import List, Tuple, Dict, Any
import numpy as np
import faiss
from loguru import logger

from src.config import settings
from src.models import JiraTicket


class VectorStore:
    """FAISS-based vector store for similarity search"""
    
    def __init__(self):
        """Initialize FAISS index"""
        self.index_path = settings.vector_store_path / f"{settings.faiss_index_name}.index"
        self.metadata_path = settings.vector_store_path / f"{settings.faiss_index_name}_metadata.pkl"
        self.index = None
        self.metadata: List[Dict[str, Any]] = []
        self.dimension = 384  # Dimension for all-MiniLM-L6-v2
        
        # Load existing index if available
        if self.index_path.exists():
            self.load()
        else:
            self._initialize_index()
    
    def _initialize_index(self):
        """Initialize a new FAISS index"""
        self.index = faiss.IndexFlatL2(self.dimension)
        logger.info(f"Initialized new FAISS index with dimension {self.dimension}")
    
    def add_tickets(self, tickets: List[JiraTicket], embeddings: List[List[float]]):
        """
        Add tickets and their embeddings to the vector store
        
        Args:
            tickets: List of JiraTicket dictionaries
            embeddings: List of embedding vectors
        """
        if len(tickets) != len(embeddings):
            raise ValueError("Number of tickets must match number of embeddings")
        
        # Convert embeddings to numpy array
        embeddings_array = np.array(embeddings, dtype=np.float32)
        
        # Add to FAISS index
        self.index.add(embeddings_array)
        
        # Store metadata
        self.metadata.extend(tickets)
        
        logger.info(f"Added {len(tickets)} tickets to vector store")
    
    def search(
        self,
        query_embedding: List[float],
        k: int = 5,
        threshold: float = None
    ) -> List[Tuple[JiraTicket, float]]:
        """
        Search for similar tickets
        
        Args:
            query_embedding: Query embedding vector
            k: Number of results to return
            threshold: Similarity threshold (optional)
        
        Returns:
            List of (ticket, similarity_score) tuples
        """
        if self.index is None or self.index.ntotal == 0:
            logger.warning("Vector store is empty")
            return []
        
        # Convert query to numpy array
        query_array = np.array([query_embedding], dtype=np.float32)
        
        # Search
        distances, indices = self.index.search(query_array, min(k, self.index.ntotal))
        
        # Convert distances to similarity scores (lower distance = higher similarity)
        # Normalize: similarity = 1 / (1 + distance)
        similarities = 1 / (1 + distances[0])
        
        results = []
        all_candidates = []
        for idx, similarity in zip(indices[0], similarities):
            if idx < len(self.metadata):
                ticket = self.metadata[idx].copy()
                ticket['similarity_score'] = float(similarity)
                all_candidates.append((ticket['key'], similarity))
                
                # Apply threshold if specified
                if threshold is None or similarity >= threshold:
                    results.append((ticket, float(similarity)))
        
        # Log all candidates with their scores
        if all_candidates:
            logger.info(f"Similarity scores: {[(k, f'{s:.4f}') for k, s in all_candidates]}, threshold={threshold}")
        
        logger.info(f"Found {len(results)} similar tickets out of {len(indices[0])} candidates (threshold={threshold})")
        return results
    
    def save(self):
        """Save FAISS index and metadata to disk"""
        if self.index is None:
            logger.warning("No index to save")
            return
        
        # Save FAISS index
        faiss.write_index(self.index, str(self.index_path))
        
        # Save metadata
        with open(self.metadata_path, 'wb') as f:
            pickle.dump(self.metadata, f)
        
        logger.info(f"Saved vector store with {self.index.ntotal} vectors")
    
    def load(self):
        """Load FAISS index and metadata from disk"""
        try:
            # Load FAISS index
            self.index = faiss.read_index(str(self.index_path))
            
            # Load metadata
            with open(self.metadata_path, 'rb') as f:
                self.metadata = pickle.load(f)
            
            logger.info(f"Loaded vector store with {self.index.ntotal} vectors")
            
        except Exception as e:
            logger.error(f"Error loading vector store: {e}")
            self._initialize_index()
    
    def clear(self):
        """Clear all data from vector store"""
        self._initialize_index()
        self.metadata = []
        logger.info("Cleared vector store")
    
    def rebuild(self, tickets: List[JiraTicket], embeddings: List[List[float]]):
        """
        Rebuild the entire vector store from scratch
        
        Args:
            tickets: List of all tickets
            embeddings: List of all embeddings
        """
        self.clear()
        self.add_tickets(tickets, embeddings)
        self.save()
        logger.info(f"Rebuilt vector store with {len(tickets)} tickets")

