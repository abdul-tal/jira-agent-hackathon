"""Jira operation tools for LangGraph agents"""

from typing import Optional, List
from langchain.tools import tool
from loguru import logger

from src.services import JiraService
from src.models import JiraTicket


# Global Jira service instance
_jira_service = None


def get_jira_service() -> JiraService:
    """Get or create Jira service instance"""
    global _jira_service
    if _jira_service is None:
        _jira_service = JiraService()
    return _jira_service


@tool
def create_jira_ticket_tool(
    summary: str,
    description: str,
    issue_type: str = "Task",
    priority: str = "Medium",
    labels: Optional[str] = None
) -> dict:
    """
    Create a new Jira ticket.
    
    Args:
        summary: Brief title of the ticket
        description: Detailed description of the issue
        issue_type: Type of ticket (Task, Bug, Story, Epic)
        priority: Priority level (Highest, High, Medium, Low, Lowest)
        labels: Comma-separated labels (optional)
    
    Returns:
        Dictionary containing the created ticket information
    """
    try:
        service = get_jira_service()
        
        # Parse labels if provided
        label_list = [l.strip() for l in labels.split(",")] if labels else None
        
        ticket = service.create_ticket(
            summary=summary,
            description=description,
            issue_type=issue_type,
            priority=priority,
            labels=label_list
        )
        
        return {
            "success": True,
            "ticket": ticket,
            "message": f"Successfully created ticket {ticket['key']}"
        }
        
    except Exception as e:
        logger.error(f"Error creating ticket: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to create ticket: {str(e)}"
        }


@tool
def update_jira_ticket_tool(
    ticket_key: str,
    summary: Optional[str] = None,
    description: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None
) -> dict:
    """
    Update an existing Jira ticket.
    
    Args:
        ticket_key: The Jira ticket key (e.g., PROJ-123)
        summary: New summary/title (optional)
        description: New description (optional)
        status: New status (To Do, In Progress, Done, etc.) (optional)
        priority: New priority level (optional)
    
    Returns:
        Dictionary containing the updated ticket information
    """
    try:
        service = get_jira_service()
        
        ticket = service.update_ticket(
            ticket_key=ticket_key,
            summary=summary,
            description=description,
            status=status,
            priority=priority
        )
        
        return {
            "success": True,
            "ticket": ticket,
            "message": f"Successfully updated ticket {ticket_key}"
        }
        
    except Exception as e:
        logger.error(f"Error updating ticket: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to update ticket: {str(e)}"
        }


@tool
def get_jira_ticket_tool(ticket_key: str) -> dict:
    """
    Retrieve information about a specific Jira ticket.
    
    Args:
        ticket_key: The Jira ticket key (e.g., PROJ-123)
    
    Returns:
        Dictionary containing the ticket information
    """
    try:
        service = get_jira_service()
        ticket = service.get_ticket(ticket_key)
        
        if ticket:
            return {
                "success": True,
                "ticket": ticket,
                "message": f"Successfully retrieved ticket {ticket_key}"
            }
        else:
            return {
                "success": False,
                "message": f"Ticket {ticket_key} not found"
            }
        
    except Exception as e:
        logger.error(f"Error retrieving ticket: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to retrieve ticket: {str(e)}"
        }

