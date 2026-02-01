# sample_payload.py
# Sample payloads for testing Jira agent

sample_payload = {
    # Remove 'issueKey' for create, add 'issueKey' for update
    "action": "update_ticket",  # or "create_ticket"
    "projectKey": "SCRUM",
    "summary": "Implement user authentication feature Final",
    "description": "Need to add OAuth2 authentication to the application\n\nRequirements:\n- Support Google and GitHub login\n- Session management\n- Secure token storage",
    "issueType": "Task",
    "issueKey": "SCRUM-10" 
    # "issueKey": "SCRUM-6"  # Uncomment for update
}
