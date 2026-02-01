# jira agents
# this agent doesn't take any decision
# it only executes create or update based on action field
# action is provided by orchestrator agent

from typing import Dict, Any, Literal, TypedDict
from pydantic import BaseModel, Field
import sys
import os

# Add parent directory to path to import services
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.jira_services import (
    create_jira_ticket,
    update_jira_ticket_with_comment,
    get_jira_service
)


class JiraAgentState(TypedDict, total=False):
    """
    State definition for Jira Agent using TypedDict
    
    Fields:
        action: The action to perform (e.g., 'create_ticket', 'add_comment')
        summary: Ticket summary/title
        description: Ticket description or comment text
        projectKey: Jira project key (e.g., 'PROJ')
        issueType: Issue type (e.g., 'Task', 'Bug', 'Story')
        issueKey: Existing issue key for updates (e.g., 'PROJ-123')
    """
    action: str
    summary: str
    description: str
    projectKey: str
    issueType: str
    issueKey: str


async def execute_create_ticket_action(state: JiraAgentState) -> str:
    """
    Function to execute create ticket action using Jira service
    
    Args:
        state: JiraAgentState containing action details
        
    Returns:
        str: The created issue key (e.g., "PROJ-123")
        
    Raises:
        ValueError: If required fields are missing
    """
    # Validate required fields
    if not state.get("projectKey"):
        raise ValueError("projectKey is required for create_ticket action")
    if not state.get("summary"):
        raise ValueError("summary is required for create_ticket action")
    if not state.get("description"):
        raise ValueError("description is required for create_ticket action")
    
    # Execute create ticket using Jira service
    issue_key = await create_jira_ticket(
        project_key=state["projectKey"],
        summary=state["summary"],
        description=state["description"],
        issue_type=state.get("issueType", "Task")
    )
    
    return issue_key


async def execute_update_ticket_action(state: JiraAgentState) -> bool:
    """
    Function to execute update ticket action using Jira service
    
    Args:
        state: JiraAgentState containing action details
        
    Returns:
        bool: True if update (comment) was successful
        
    Raises:
        ValueError: If required fields are missing
    """
    # Validate required fields
    if not state.get("issueKey"):
        raise ValueError("issueKey is required for update_ticket action")
    if not state.get("description"):
        raise ValueError("description is required for update_ticket action")
    
    # Execute update ticket (add comment) using Jira service
    success = await update_jira_ticket_with_comment(
        issue_key=state["issueKey"],
        comment=state["description"]
    )
    
    return success


class JiraAction(BaseModel):
    """Model for Jira actions provided by orchestrator agent"""
    action: Literal["create_ticket", "add_comment"] = Field(
        description="The action to perform: 'create_ticket' or 'add_comment'"
    )
    project_key: str | None = Field(
        default=None,
        description="Project key (required for create_ticket)"
    )
    summary: str | None = Field(
        default=None,
        description="Ticket summary/title (required for create_ticket)"
    )
    description: str | None = Field(
        default=None,
        description="Ticket description (required for create_ticket)"
    )
    issue_type: str | None = Field(
        default="Task",
        description="Issue type: Task, Bug, Story, etc. (for create_ticket)"
    )
    issue_key: str | None = Field(
        default=None,
        description="Issue key like PROJ-123 (required for add_comment)"
    )
    comment: str | None = Field(
        default=None,
        description="Comment text (required for add_comment)"
    )


class JiraAgent:
    """
    Jira Agent - Executes Jira operations without decision-making
    
    This agent is a simple executor that performs actions as instructed
    by an orchestrator agent. It does not make any decisions about what
    actions to take or when to take them.
    """
    
    def __init__(self):
        """Initialize the Jira Agent"""
        self.name = "JiraAgent"
        self.description = "Executes Jira ticket creation and updates based on orchestrator commands"
    
    async def execute_action(self, action: JiraAction) -> Dict[str, Any]:
        """
        Execute a Jira action based on orchestrator command
        
        Args:
            action: JiraAction object containing the action and parameters
        
        Returns:
            Dict containing the result of the action
        
        Raises:
            ValueError: If required parameters are missing or action is invalid
        """
        if action.action == "create_ticket":
            return await self._create_ticket(action)
        elif action.action == "add_comment":
            return await self._add_comment(action)
        else:
            raise ValueError(f"Unknown action: {action.action}")
    
    async def _create_ticket(self, action: JiraAction) -> Dict[str, Any]:
        """
        Execute create ticket action
        
        Args:
            action: JiraAction with create_ticket parameters
        
        Returns:
            Dict with success status and created issue key
        """
        # Validate required fields
        if not action.project_key:
            raise ValueError("project_key is required for create_ticket action")
        if not action.summary:
            raise ValueError("summary is required for create_ticket action")
        if not action.description:
            raise ValueError("description is required for create_ticket action")
        
        # Execute the action
        issue_key = await create_jira_ticket(
            project_key=action.project_key,
            summary=action.summary,
            description=action.description,
            issue_type=action.issue_type or "Task"
        )
        
        return {
            "success": True,
            "action": "create_ticket",
            "issue_key": issue_key,
            "message": f"Successfully created ticket: {issue_key}"
        }
    
    async def _add_comment(self, action: JiraAction) -> Dict[str, Any]:
        """
        Execute add comment action
        
        Args:
            action: JiraAction with add_comment parameters
        
        Returns:
            Dict with success status
        """
        # Validate required fields
        if not action.issue_key:
            raise ValueError("issue_key is required for add_comment action")
        if not action.comment:
            raise ValueError("comment is required for add_comment action")
        
        # Execute the action
        success = await update_jira_ticket_with_comment(
            issue_key=action.issue_key,
            comment=action.comment
        )
        
        return {
            "success": success,
            "action": "add_comment",
            "issue_key": action.issue_key,
            "message": f"Successfully added comment to {action.issue_key}"
        }
    
    async def execute_from_dict(self, action_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a Jira action from a dictionary (convenience method)
        
        Args:
            action_dict: Dictionary containing action and parameters
        
        Returns:
            Dict containing the result of the action
        """
        action = JiraAction(**action_dict)
        return await self.execute_action(action)


# Convenience function to get a JiraAgent instance
def get_jira_agent() -> JiraAgent:
    """Get an instance of JiraAgent"""
    return JiraAgent()


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def test_agent():
        agent = get_jira_agent()
        
        # Example 1: Create a ticket (as instructed by orchestrator)
        create_action = JiraAction(
            action="create_ticket",
            project_key="PROJ",
            summary="Test ticket from agent",
            description="This ticket was created by the Jira agent based on orchestrator command",
            issue_type="Task"
        )
        
        try:
            result = await agent.execute_action(create_action)
            print(f"✓ {result['message']}")
            created_key = result['issue_key']
            
            # Example 2: Add a comment (as instructed by orchestrator)
            comment_action = JiraAction(
                action="add_comment",
                issue_key=created_key,
                comment="This comment was added by the Jira agent"
            )
            
            result = await agent.execute_action(comment_action)
            print(f"✓ {result['message']}")
            
        except ValueError as e:
            print(f"✗ Configuration error: {e}")
        except Exception as e:
            print(f"✗ Error: {e}")
    
    # asyncio.run(test_agent())
    print("JiraAgent initialized. Uncomment asyncio.run() to test.")
