# jira service wrapper
# this file should contain functions to create and update jira tickets
# authentication should be done using email and api token from environment variables
# use jira cloud rest api v3

import os
import logging
import httpx
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv

from .external_api import send_jira_notification

# Load environment variables
load_dotenv()


def text_to_adf(text: str) -> Dict[str, Any]:
    """
    Convert plain text to Atlassian Document Format (ADF)
    
    Args:
        text: Plain text string (can include newlines)
    
    Returns:
        Dict in ADF format compatible with Jira Cloud API v3
    """
    # Split text by newlines to create separate paragraphs
    lines = text.split('\n')
    
    content = []
    for line in lines:
        if line.strip():  # Only add non-empty lines
            content.append({
                "type": "paragraph",
                "content": [
                    {
                        "type": "text",
                        "text": line
                    }
                ]
            })
        else:
            # Add empty paragraph for blank lines
            content.append({
                "type": "paragraph",
                "content": []
            })
    
    return {
        "type": "doc",
        "version": 1,
        "content": content if content else [{
            "type": "paragraph",
            "content": [{"type": "text", "text": ""}]
        }]
    }


def create_adf_document(content_blocks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Create a custom Atlassian Document Format (ADF) document
    
    Args:
        content_blocks: List of ADF content blocks (paragraphs, headings, lists, etc.)
    
    Returns:
        Dict in ADF format
    
    Example:
        content_blocks = [
            {
                "type": "heading",
                "attrs": {"level": 1},
                "content": [{"type": "text", "text": "Title"}]
            },
            {
                "type": "paragraph",
                "content": [{"type": "text", "text": "Description text"}]
            }
        ]
    """
    return {
        "type": "doc",
        "version": 1,
        "content": content_blocks
    }


class JiraService:
    """Wrapper for Jira Cloud REST API v3"""
    
    def __init__(self):
        """Initialize Jira service with credentials from environment variables"""
        self.email = os.getenv("JIRA_EMAIL")
        self.api_token = os.getenv("JIRA_API_TOKEN")
        self.base_url = os.getenv("JIRA_BASE_URL")  # e.g., https://your-domain.atlassian.net
        
        if not all([self.email, self.api_token, self.base_url]):
            raise ValueError(
                "Missing required environment variables: JIRA_EMAIL, JIRA_API_TOKEN, JIRA_BASE_URL"
            )
        
        self.api_url = f"{self.base_url}/rest/api/3"
        self.auth = (self.email, self.api_token)
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
    
    async def create_ticket(
        self,
        project_key: str,
        summary: str,
        description: str,
        issue_type: str = "Task",
        priority: Optional[str] = None,
        assignee: Optional[str] = None,
        labels: Optional[List[str]] = None,
        additional_fields: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new Jira ticket
        
        Args:
            project_key: The project key (e.g., "PROJ")
            summary: The issue summary/title
            description: The issue description (plain text - will be converted to ADF)
            issue_type: The issue type (default: "Task")
            priority: Priority name (e.g., "High", "Medium", "Low")
            assignee: Account ID of the assignee
            labels: List of labels to add
            additional_fields: Additional custom fields to include
            
        Returns:
            Dict containing the created issue details including key and id
        """
        fields = {
            "project": {"key": project_key},
            "summary": summary,
            "description": text_to_adf(description),  # Convert to Atlassian Document Format
            "issuetype": {"name": issue_type}
        }
        
        if priority:
            fields["priority"] = {"name": priority}
        
        if assignee:
            fields["assignee"] = {"accountId": assignee}
        
        if labels:
            fields["labels"] = labels
        
        if additional_fields:
            fields.update(additional_fields)
        
        payload = {"fields": fields}
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/issue",
                json=payload,
                auth=self.auth,
                headers=self.headers
            )
            response.raise_for_status()
            data = response.json()

            # Try to send notification about created ticket (best-effort)
            try:
                issue_key = data.get("key")
                issue_url = f"{self.base_url}/browse/{issue_key}" if issue_key else None
                await send_jira_notification(
                    action="create",
                    issue_key=issue_key,
                    issue_url=issue_url,
                    summary=summary,
                    description=description,
                    extra={"api_response": data}
                )
            except Exception as e:
                logger = logging.getLogger(__name__)
                logger.exception(f"Failed to send notification for created issue {data.get('key')}: {e}")

            return data

    async def update_ticket(
        self,
        issue_key: str,
        summary: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        assignee: Optional[str] = None,
        labels: Optional[List[str]] = None,
        additional_fields: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update an existing Jira ticket
        
        Args:
            issue_key: The issue key (e.g., "PROJ-123")
            summary: Updated summary/title
            description: Updated description
            status: Status name to transition to
            priority: Priority name to update
            assignee: Account ID of the new assignee
            labels: List of labels to set
            additional_fields: Additional custom fields to update
            
        Returns:
            True if update was successful
        """
        fields = {}
        
        if summary:
            fields["summary"] = summary
        
        if description:
            fields["description"] = text_to_adf(description)  # Convert to Atlassian Document Format
        
        if priority:
            fields["priority"] = {"name": priority}
        
        if assignee:
            fields["assignee"] = {"accountId": assignee}
        
        if labels:
            fields["labels"] = labels
        
        if additional_fields:
            fields.update(additional_fields)
        
        if fields:
            payload = {"fields": fields}
            async with httpx.AsyncClient() as client:
                response = await client.put(
                    f"{self.api_url}/issue/{issue_key}",
                    json=payload,
                    auth=self.auth,
                    headers=self.headers
                )
                response.raise_for_status()

        # Handle status transition separately if provided
        if status:
            await self._transition_issue(issue_key, status)

        # Fetch updated issue details for notification (best effort)
        try:
            issue = await self.get_ticket(issue_key)
            issue_url = f"{self.base_url}/browse/{issue_key}"
            description_text = None
            if issue.get("fields", {}).get("description"):
                description_text = "".join(
                    part.get("text", "")
                    for para in issue.get("fields", {}).get("description", {}).get("content", [])
                    for part in para.get("content", [])
                )
            await send_jira_notification(
                action="update",
                issue_key=issue_key,
                issue_url=issue_url,
                summary=issue.get("fields", {}).get("summary"),
                description=description_text,
                extra={"updated_fields": list(fields.keys())}
            )
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.exception(f"Failed to send notification for updated issue {issue_key}: {e}")

        return True
    async def _transition_issue(self, issue_key: str, status: str) -> bool:
        """
        Transition an issue to a new status
        
        Args:
            issue_key: The issue key
            status: The target status name
            
        Returns:
            True if transition was successful
        """
        # Get available transitions
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_url}/issue/{issue_key}/transitions",
                auth=self.auth,
                headers=self.headers
            )
            response.raise_for_status()
            transitions = response.json()["transitions"]
        
        # Find the transition ID for the target status
        transition_id = None
        for transition in transitions:
            if transition["to"]["name"].lower() == status.lower():
                transition_id = transition["id"]
                break
        
        if not transition_id:
            raise ValueError(f"No transition available to status '{status}'")
        
        # Perform the transition
        payload = {"transition": {"id": transition_id}}
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/issue/{issue_key}/transitions",
                json=payload,
                auth=self.auth,
                headers=self.headers
            )
            response.raise_for_status()
        
        return True
    
    async def get_ticket(self, issue_key: str) -> Dict[str, Any]:
        """
        Get details of a specific ticket
        
        Args:
            issue_key: The issue key (e.g., "PROJ-123")
            
        Returns:
            Dict containing the issue details
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_url}/issue/{issue_key}",
                auth=self.auth,
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
    
    async def add_comment(self, issue_key: str, comment: str) -> Dict[str, Any]:
        """
        Add a comment to a ticket
        
        Args:
            issue_key: The issue key (e.g., "PROJ-123")
            comment: The comment text (plain text - will be converted to ADF)
            
        Returns:
            Dict containing the created comment details
        """
        payload = {
            "body": text_to_adf(comment)  # Convert to Atlassian Document Format
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/issue/{issue_key}/comment",
                json=payload,
                auth=self.auth,
                headers=self.headers
            )
            response.raise_for_status()
            data = response.json()

        # Try to send notification about the comment being added (best-effort)
        try:
            issue_url = f"{self.base_url}/browse/{issue_key}"
            await send_jira_notification(
                action="comment",
                issue_key=issue_key,
                issue_url=issue_url,
                summary=None,
                description=comment,
                extra={"comment_id": data.get("id")}
            )
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.exception(f"Failed to send notification for comment on {issue_key}: {e}")

        return data
    
    async def search_tickets(
        self,
        jql: str,
        fields: Optional[List[str]] = None,
        max_results: int = 50
    ) -> Dict[str, Any]:
        """
        Search for tickets using JQL
        
        Args:
            jql: JQL query string
            fields: List of fields to return (default: all)
            max_results: Maximum number of results to return
            
        Returns:
            Dict containing search results
        """
        params = {
            "jql": jql,
            "maxResults": max_results
        }
        
        if fields:
            params["fields"] = ",".join(fields)
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_url}/search",
                params=params,
                auth=self.auth,
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()


# Convenience function to get a JiraService instance
def get_jira_service() -> JiraService:
    """Get an instance of JiraService"""
    return JiraService()


async def create_jira_ticket(
    project_key: str,
    summary: str,
    description: str,
    issue_type: str
) -> str:
    """
    Function to create Jira Ticket
    
    Args:
        project_key: The project key (e.g., "PROJ")
        summary: The issue summary/title
        description: The issue description
        issue_type: The issue type (e.g., "Task", "Bug", "Story")
    
    Returns:
        str: The created issue key (e.g., "PROJ-123")
    """
    jira = get_jira_service()
    result = await jira.create_ticket(
        project_key=project_key,
        summary=summary,
        description=description,
        issue_type=issue_type
    )
    return result["key"]


async def update_jira_ticket_with_comment(
    issue_key: str,
    comment: str
) -> bool:
    """
    Function to update Jira ticket by adding a comment
    
    Args:
        issue_key: The issue key (e.g., "PROJ-123")
        comment: The comment text to add
    
    Returns:
        bool: True if comment was added successfully
    """
    jira = get_jira_service()
    await jira.add_comment(issue_key=issue_key, comment=comment)
    return True
