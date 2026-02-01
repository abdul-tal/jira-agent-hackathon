"""Node functions for the Similarity Agent graph"""

import json
from datetime import datetime
from typing import Dict, Any
from loguru import logger
from langchain_openai import ChatOpenAI

from similarity_agent.state import SimilarityAgentState, MatchedTicket
from similarity_agent.prompts import (
    QUERY_ANALYZER_PROMPT,
    RESULT_ANALYZER_PROMPT
)

# Import services from main project
import sys
from pathlib import Path

# Add parent directory to path for imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.services.vector_store import VectorStore
from src.services.embeddings_service import EmbeddingsService
from src.config.settings import settings

print('open ai key: ', settings.openai_api_key)

# Initialize services
llm = ChatOpenAI(
    model=settings.openai_model,
    temperature=0,
    openai_api_key=settings.openai_api_key
)

vector_store = VectorStore()
embeddings_service = EmbeddingsService()


def analyze_query_node(state: SimilarityAgentState) -> SimilarityAgentState:
    """
    Analyze the user query to extract key components and keywords.
    
    This node uses an LLM to understand what the user is looking for
    and extract relevant information for searching.
    """
    logger.info("Node: Analyzing user query")
    
    query = state["user_query"]
    
    try:
        # Use LLM to analyze the query
        prompt = QUERY_ANALYZER_PROMPT.format(query=query)
        response = llm.invoke(prompt)
        
        # Parse JSON response
        content = response.content
        
        # Extract JSON from markdown code blocks if present
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        analysis = json.loads(content)
        
        state["query_analysis"] = analysis
        state["search_keywords"] = analysis.get("keywords", [])
        
        logger.info(f"Query analysis complete: {analysis.get('main_topic', 'Unknown')}")
        
    except Exception as e:
        logger.error(f"Error analyzing query: {e}")
        # Fallback: use the query as-is
        state["query_analysis"] = {
            "main_topic": query,
            "keywords": query.split()
        }
        state["search_keywords"] = query.split()
    
    return state


def search_tickets_node(state: SimilarityAgentState) -> SimilarityAgentState:
    """
    Search for similar tickets using vector similarity.
    
    This node performs semantic search on the vector store to find
    tickets that match the user's query.
    """
    logger.info("Node: Searching for similar tickets")
    
    query = state["user_query"]
    max_results = state.get("max_results", 5)
    
    try:
        # Generate embedding for the query
        logger.info("Generating query embedding...")
        query_embedding = embeddings_service.generate_embedding(query)
        
        # Search vector store
        logger.info(f"Searching vector store (max_results={max_results})...")
        results = vector_store.search(
            query_embedding=query_embedding,
            k=max_results,
            threshold=settings.similarity_threshold
        )
        
        # Format results
        matched_tickets = []
        for ticket_dict, score in results:
            matched_ticket: MatchedTicket = {
                "key": ticket_dict.get("key", ""),
                "summary": ticket_dict.get("summary", ""),
                "description": ticket_dict.get("description", ""),
                "issue_type": ticket_dict.get("issue_type", ""),
                "priority": ticket_dict.get("priority", ""),
                "status": ticket_dict.get("status", ""),
                "labels": ticket_dict.get("labels", []),
                "similarity_score": round(score, 4),
                "match_reason": None  # Will be filled by result analyzer
            }
            matched_tickets.append(matched_ticket)
        
        state["matched_tickets"] = matched_tickets
        state["total_matches"] = len(matched_tickets)
        state["has_matches"] = len(matched_tickets) > 0
        
        if matched_tickets:
            state["best_match"] = matched_tickets[0]  # Highest score
            logger.info(f"Found {len(matched_tickets)} matching tickets")
        else:
            state["best_match"] = None
            logger.info("No matching tickets found")
        
    except Exception as e:
        logger.error(f"Error searching tickets: {e}")
        state["matched_tickets"] = []
        state["total_matches"] = 0
        state["has_matches"] = False
        state["best_match"] = None
        state["error"] = str(e)
    
    return state


def analyze_results_node(state: SimilarityAgentState) -> SimilarityAgentState:
    """
    Analyze search results and generate a helpful response.
    
    This node uses an LLM to understand why tickets matched and
    generate a clear, actionable response for the user.
    """
    logger.info("Node: Analyzing search results")
    
    query = state["user_query"]
    matched_tickets = state["matched_tickets"]
    
    if not matched_tickets:
        # No matches found
        state["confidence_level"] = "none"
        state["response_message"] = (
            f"No existing tickets found that match your query: '{query}'. "
            f"This appears to be a new issue or request. You may want to create a new ticket."
        )
        logger.info("No matches to analyze")
        return state
    
    try:
        # Format search results for analysis
        results_summary = []
        for ticket in matched_tickets:
            results_summary.append({
                "key": ticket["key"],
                "summary": ticket["summary"],
                "description": ticket["description"][:200] + "..." if len(ticket["description"]) > 200 else ticket["description"],
                "type": ticket["issue_type"],
                "priority": ticket["priority"],
                "status": ticket["status"],
                "similarity_score": ticket["similarity_score"]
            })
        
        # Use LLM to analyze results
        prompt = RESULT_ANALYZER_PROMPT.format(
            query=query,
            search_results=json.dumps(results_summary, indent=2)
        )
        response = llm.invoke(prompt)
        
        # Parse JSON response
        content = response.content
        
        # Extract JSON from markdown code blocks if present
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        analysis = json.loads(content)
        
        # Update state with analysis
        state["confidence_level"] = analysis.get("confidence_level", "medium")
        state["response_message"] = analysis.get("response_message", "")
        
        # Add match reasons to tickets
        match_explanations = analysis.get("match_explanations", {})
        for ticket in state["matched_tickets"]:
            if ticket["key"] in match_explanations:
                ticket["match_reason"] = match_explanations[ticket["key"]]
        
        logger.info(f"Result analysis complete: confidence={state['confidence_level']}")
        
    except Exception as e:
        logger.error(f"Error analyzing results: {e}")
        # Fallback response
        state["confidence_level"] = "medium"
        best_match = state["best_match"]
        if best_match:
            state["response_message"] = (
                f"Found {len(matched_tickets)} similar ticket(s). "
                f"The most similar is {best_match['key']}: {best_match['summary']} "
                f"(similarity: {best_match['similarity_score']:.2%})"
            )
        else:
            state["response_message"] = f"Found {len(matched_tickets)} potentially related ticket(s)."
    
    return state


def format_response_node(state: SimilarityAgentState) -> SimilarityAgentState:
    """
    Format the final response with all ticket details.
    
    This node creates a comprehensive, well-formatted response
    that includes all matched tickets and their complete details.
    The matched tickets are returned to the user for review.
    """
    logger.info("Node: Formatting final response with matched tickets")
    
    matched_tickets = state["matched_tickets"]
    response_parts = [state["response_message"]]
    
    if matched_tickets:
        response_parts.append(f"\n\n**📋 Returning {len(matched_tickets)} Matched Ticket{'s' if len(matched_tickets) > 1 else ''}:**\n")
        
        for i, ticket in enumerate(matched_tickets, 1):
            # Format ticket details clearly
            ticket_info = [
                f"\n{i}. **{ticket['key']}** (Similarity: {ticket['similarity_score']:.1%})",
                f"   - **Summary**: {ticket['summary']}",
                f"   - **Type**: {ticket['issue_type']} | **Priority**: {ticket['priority']} | **Status**: {ticket['status']}"
            ]
            
            # Add description (truncated if too long)
            desc = ticket['description']
            if len(desc) > 200:
                ticket_info.append(f"   - **Description**: {desc[:200]}...")
            else:
                ticket_info.append(f"   - **Description**: {desc}")
            
            # Add match reason if available
            if ticket.get("match_reason"):
                ticket_info.append(f"   - **Why it matched**: {ticket['match_reason']}")
            
            # Add labels if available
            if ticket.get("labels"):
                ticket_info.append(f"   - **Labels**: {', '.join(ticket['labels'])}")
            
            response_parts.append("\n".join(ticket_info))
        
        # Add helpful footer
        response_parts.append(
            f"\n\n💡 **Next Steps**: Review the above ticket{'s' if len(matched_tickets) > 1 else ''} "
            f"to see if {'any of them address' if len(matched_tickets) > 1 else 'it addresses'} your needs. "
            f"You can add comments, link to {'them' if len(matched_tickets) > 1 else 'it'}, or create a new ticket if needed."
        )
    else:
        response_parts.append(
            f"\n\n💡 **Next Steps**: No existing tickets found. You should create a new ticket for this issue."
        )
    
    state["response_message"] = "\n".join(response_parts)
    state["timestamp"] = datetime.now().isoformat()
    
    logger.info(f"Response formatted successfully with {len(matched_tickets)} ticket(s)")
    
    return state

