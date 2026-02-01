"""Jira agent for creating and updating tickets"""

import sys
import os
from loguru import logger

from src.models import AgentState

# Add jira-agents to path
jira_agents_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    'jira-agents'
)
sys.path.insert(0, jira_agents_path)

from services.jira_services import create_jira_ticket, update_jira_ticket_with_comment


async def jira_node(state: AgentState, config: dict = None) -> AgentState:
    """
    Handle Jira ticket operations (create/update)
    
    Args:
        state: Current agent state
        config: LangGraph config containing runtime context
    
    Returns:
        Updated state with Jira operation results
    """
    logger.info("Jira agent: Processing ticket operation")
    
    # Get event queue for streaming
    event_queue = config.get("configurable", {}).get("event_queue") if config else None
    
    intent = state.get("intent", "create")
    ticket_data = state.get("ticket_data", {})
    
    try:
        if intent == "create":
            # Emit creating event
            if event_queue:
                await event_queue.put({'event': 'jira_create', 'message': '🎫 Creating Jira ticket...'})
            
            # Extract ticket information from state
            project_key = ticket_data.get("project_key", "SCRUM")  # Default project
            
            # Ensure summary is never empty - use user query as fallback
            summary = ticket_data.get("summary", "")
            if not summary or summary.strip() == "":
                summary = state["user_query"][:100]  # Truncate to 100 chars for summary
            
            # Ensure description is never empty - use full query as fallback
            description = ticket_data.get("description", "")
            if not description or description.strip() == "":
                description = state["user_query"]
            
            issue_type = ticket_data.get("issue_type", "Task")
            
            logger.info(f"Creating Jira ticket: {summary}")
            
            # Create the ticket
            issue_key = await create_jira_ticket(
                project_key=project_key,
                summary=summary,
                description=description,
                issue_type=issue_type
            )
            
            state["created_ticket"] = {
                "key": issue_key,
                "summary": summary,
                "description": description,
                "project": project_key,
                "type": issue_type,
                "status": "To Do",
                "priority": "Medium"
            }
            state["action_type"] = "create"
            state["final_response"] = f"Successfully created ticket {issue_key}"
            
            logger.info(f"Jira agent: Created ticket {issue_key}")
            
            # Emit success event
            if event_queue:
                await event_queue.put({
                    'event': 'ticket_created',
                    'message': f'🎉 Created ticket {issue_key}!',
                    'ticket_key': issue_key
                })
            
        elif intent == "update":
            # Emit updating event
            if event_queue:
                await event_queue.put({'event': 'jira_update', 'message': '✏️ Updating Jira ticket...'})
            
            # Extract update information from state
            issue_key = ticket_data.get("issue_key")
            comment = ticket_data.get("comment", state["user_query"])
            
            if not issue_key:
                raise ValueError("Issue key is required for update operations")
            
            logger.info(f"Updating Jira ticket: {issue_key}")
            
            # Add comment to the ticket
            success = await update_jira_ticket_with_comment(
                issue_key=issue_key,
                comment=comment
            )
            
            if success:
                state["action_type"] = "update"
                state["final_response"] = f"Successfully updated ticket {issue_key}"
                logger.info(f"Jira agent: Updated ticket {issue_key}")
                
                # Emit success event
                if event_queue:
                    await event_queue.put({
                        'event': 'ticket_updated',
                        'message': f'✨ Updated ticket {issue_key}!',
                        'ticket_key': issue_key
                    })
            else:
                raise Exception("Failed to update ticket")
        
        else:
            raise ValueError(f"Unknown intent: {intent}")
        
    except Exception as e:
        logger.error(f"Jira agent error: {e}")
        state["error"] = str(e)
        state["final_response"] = f"I encountered an error: {str(e)}"
    
    return state

