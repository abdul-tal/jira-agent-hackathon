"""Jira API service for fetching and managing tickets"""

from typing import List, Dict, Any, Optional
from jira import JIRA
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from src.config import settings
from src.models import JiraTicket


class JiraService:
    """Service for interacting with Jira API"""
    
    def __init__(self):
        """Initialize Jira client"""
        self.client = JIRA(
            server=settings.jira_url,
            basic_auth=(settings.jira_email, settings.jira_api_token)
        )
        self.project_key = settings.jira_project_key
        logger.info(f"Jira service initialized for project: {self.project_key}")
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def fetch_all_tickets(self) -> List[JiraTicket]:
        """
        Fetch all tickets from Jira project
        
        Returns:
            List of JiraTicket dictionaries
        """
        try:
            jql_query = f'project = {self.project_key} ORDER BY updated DESC'
            issues = self.client.search_issues(
                jql_query,
                maxResults=False,
                fields='summary,description,status,priority,assignee,created,updated,issuetype,labels'
            )
            
            tickets = []
            for issue in issues:
                ticket = self._issue_to_ticket(issue)
                tickets.append(ticket)
            
            logger.info(f"Fetched {len(tickets)} tickets from Jira")
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

