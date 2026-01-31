"""Jira API service for fetching and managing tickets"""

from typing import List, Dict, Any, Optional
from jira import JIRA
import requests
from requests.auth import HTTPBasicAuth
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from src.config import settings
from src.models import JiraTicket


class JiraService:
    """Service for interacting with Jira API"""
    
    def __init__(self):
        """Initialize Jira client with API v3"""
        # Configure JIRA client to use API v3
        options = {
            'server': settings.jira_url,
            'rest_api_version': '3'  # Use API v3 instead of deprecated v2
        }
        self.client = JIRA(
            options=options,
            basic_auth=(settings.jira_email, settings.jira_api_token)
        )
        self.project_key = settings.jira_project_key
        logger.info(f"Jira service initialized for project: {self.project_key} (API v3)")
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def fetch_all_tickets(self) -> List[JiraTicket]:
        """
        Fetch all tickets from Jira project using the new API v3 search/jql endpoint
        
        Returns:
            List of JiraTicket dictionaries
        """
        try:
            # Use the new POST /rest/api/3/search/jql endpoint
            # Note: This endpoint uses a different format than /rest/api/3/search
            url = f"{settings.jira_url}/rest/api/3/search/jql"
            
            auth = HTTPBasicAuth(settings.jira_email, settings.jira_api_token)
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
            
            tickets = []
            start_at = 0
            max_results = 50
            
            # Paginate through all results
            while True:
                # Build payload exactly as in working curl - order matters!
                payload = {
                    "fieldsByKeys": True,
                    "jql": f"project = {self.project_key} ORDER BY updated DESC",
                    "maxResults": max_results,
                    # "startAt": start_at,
                    "fields": [
                        "summary",
                        "status",
                        "assignee",
                        "created",
                        "updated",
                        "issuetype",
                        "priority",
                        "description",
                        "labels"
                    ]
                }
                
                response = requests.post(url, json=payload, auth=auth, headers=headers)
                
                # Better error handling with response details
                if not response.ok:
                    error_detail = response.text
                    logger.error(f"Jira API Error {response.status_code}: {error_detail}")
                    logger.error(f"Request payload: {payload}")
                    response.raise_for_status()
                
                data = response.json()
                issues = data.get("issues", [])
                
                if not issues:
                    break
                
                for issue_data in issues:
                    ticket = self._api_response_to_ticket(issue_data)
                    tickets.append(ticket)
                
                # Check if there are more results
                total = data.get("total", 0)
                if start_at + len(issues) >= total:
                    break
                    
                start_at += len(issues)
            
            logger.info(f"Fetched {len(tickets)} tickets from Jira using API v3")
            return tickets
            
        except Exception as e:
            logger.error(f"Error fetching tickets from Jira: {e}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def create_ticket(
        self,
        summary: str,
        description: str,
        issue_type: str = "Task",
        priority: str = "Medium",
        labels: Optional[List[str]] = None
    ) -> JiraTicket:
        """
        Create a new Jira ticket
        
        Args:
            summary: Ticket summary
            description: Ticket description
            issue_type: Type of issue (Task, Bug, Story, etc.)
            priority: Priority level
            labels: List of labels
        
        Returns:
            Created JiraTicket
        """
        try:
            issue_dict = {
                'project': {'key': self.project_key},
                'summary': summary,
                'description': description,
                'issuetype': {'name': issue_type},
                'priority': {'name': priority}
            }
            
            if labels:
                issue_dict['labels'] = labels
            
            new_issue = self.client.create_issue(fields=issue_dict)
            ticket = self._issue_to_ticket(new_issue)
            
            logger.info(f"Created ticket: {ticket['key']}")
            return ticket
            
        except Exception as e:
            logger.error(f"Error creating ticket: {e}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def update_ticket(
        self,
        ticket_key: str,
        summary: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None
    ) -> JiraTicket:
        """
        Update an existing Jira ticket
        
        Args:
            ticket_key: Jira ticket key (e.g., PROJ-123)
            summary: New summary
            description: New description
            status: New status
            priority: New priority
        
        Returns:
            Updated JiraTicket
        """
        try:
            issue = self.client.issue(ticket_key)
            update_fields = {}
            
            if summary:
                update_fields['summary'] = summary
            if description:
                update_fields['description'] = description
            if priority:
                update_fields['priority'] = {'name': priority}
            
            if update_fields:
                issue.update(fields=update_fields)
            
            if status:
                transitions = self.client.transitions(issue)
                transition_id = None
                for t in transitions:
                    if t['name'].lower() == status.lower():
                        transition_id = t['id']
                        break
                
                if transition_id:
                    self.client.transition_issue(issue, transition_id)
            
            # Refresh issue to get updated data
            issue = self.client.issue(ticket_key)
            ticket = self._issue_to_ticket(issue)
            
            logger.info(f"Updated ticket: {ticket_key}")
            return ticket
            
        except Exception as e:
            logger.error(f"Error updating ticket {ticket_key}: {e}")
            raise
    
    def get_ticket(self, ticket_key: str) -> Optional[JiraTicket]:
        """
        Get a specific ticket by key
        
        Args:
            ticket_key: Jira ticket key
        
        Returns:
            JiraTicket or None if not found
        """
        try:
            issue = self.client.issue(ticket_key)
            return self._issue_to_ticket(issue)
        except Exception as e:
            logger.error(f"Error getting ticket {ticket_key}: {e}")
            return None
    
    def _issue_to_ticket(self, issue) -> JiraTicket:
        """Convert Jira issue object to JiraTicket dict"""
        return JiraTicket(
            key=issue.key,
            summary=issue.fields.summary,
            description=issue.fields.description or "",
            status=issue.fields.status.name,
            priority=issue.fields.priority.name if issue.fields.priority else "None",
            assignee=issue.fields.assignee.displayName if issue.fields.assignee else None,
            created=str(issue.fields.created),
            updated=str(issue.fields.updated),
            issue_type=issue.fields.issuetype.name,
            labels=issue.fields.labels or [],
            similarity_score=None
        )
    
    def _extract_description_text(self, description_field: Any) -> str:
        """Extract plain text from Jira description field (handles ADF format)"""
        if not description_field:
            return ""
        
        # If it's already a string, return it
        if isinstance(description_field, str):
            return description_field
        
        # If it's ADF (Atlassian Document Format), extract text
        if isinstance(description_field, dict):
            content = description_field.get("content", [])
            text_parts = []
            
            def extract_text(node):
                if isinstance(node, dict):
                    # Get text from text nodes
                    if node.get("type") == "text":
                        text_parts.append(node.get("text", ""))
                    # Recursively process content
                    if "content" in node:
                        for child in node["content"]:
                            extract_text(child)
                elif isinstance(node, list):
                    for item in node:
                        extract_text(item)
            
            extract_text(content)
            return " ".join(text_parts).strip()
        
        return str(description_field)
    
    def _api_response_to_ticket(self, issue_data: Dict[str, Any]) -> JiraTicket:
        """Convert API v3 response to JiraTicket dict"""
        fields = issue_data.get("fields", {})
        
        # Extract status
        status_obj = fields.get("status", {})
        status = status_obj.get("name", "Unknown") if isinstance(status_obj, dict) else "Unknown"
        
        # Extract priority
        priority_obj = fields.get("priority")
        priority = priority_obj.get("name", "None") if priority_obj and isinstance(priority_obj, dict) else "None"
        
        # Extract assignee
        assignee_obj = fields.get("assignee")
        assignee = assignee_obj.get("displayName") if assignee_obj and isinstance(assignee_obj, dict) else None
        
        # Extract issue type
        issuetype_obj = fields.get("issuetype", {})
        issue_type = issuetype_obj.get("name", "Task") if isinstance(issuetype_obj, dict) else "Task"
        
        # Extract description (handle ADF format)
        description = self._extract_description_text(fields.get("description"))
        
        return JiraTicket(
            key=issue_data.get("key", ""),
            summary=fields.get("summary", ""),
            description=description,
            status=status,
            priority=priority,
            assignee=assignee,
            created=fields.get("created", ""),
            updated=fields.get("updated", ""),
            issue_type=issue_type,
            labels=fields.get("labels", []),
            similarity_score=None
        )

