"""Similarity Agent - Find existing Jira tickets using semantic search

This module provides a LangGraph-based agent that searches for existing Jira tickets
based on user queries using vector similarity search.
"""

from similarity_agent.agent import SimilarityAgent
from similarity_agent.state import SimilarityAgentState

__all__ = ["SimilarityAgent", "SimilarityAgentState"]

