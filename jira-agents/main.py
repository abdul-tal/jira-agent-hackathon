"""
Entry point to test Jira Agent
Invoke jira agent with update and create sample payload
"""

import asyncio
from dotenv import load_dotenv
from graph.jira_graph import jira_agent

from agents.jira_agents import JiraAgentState
from sample_payload import sample_payload

# Load environment variables from .env file
load_dotenv()


async def test_create_ticket():
    """Test creating a Jira ticket"""
    print("\n" + "="*60)
    print("TEST 1: CREATE TICKET")
    print("="*60)
    
    # Sample payload for creating a ticket
    create_payload: JiraAgentState = {
        "action": "create_ticket",
        "projectKey": "SCRUM",
        "summary": "Implement user authentication feature Updated",
        "description": "Need to add OAuth2 authentication to the application\n\nRequirements:\n- Support Google and GitHub login\n- Session management\n- Secure token storage",
        "issueType": "Task",
        "issueKey": "SCRUM-6"
    }
    
    try:
        print(f"\n📝 Creating ticket...")
        print(f"   Project: {create_payload['projectKey']}")
        print(f"   Summary: {create_payload['summary']}")
        print(f"   Type: {create_payload['issueType']}")
        
        # Invoke the jira agent
        result = await jira_agent.ainvoke(create_payload)
        print(f"\n✅ SUCCESS!")
        print(f"   Created Issue: {result.get('issueKey')}")
        
        return result.get('issueKey')
        
    except ValueError as e:
        print(f"\n❌ Configuration Error: {e}")
        print("\nPlease ensure:")
        print("1. You have created a .env file (copy from .env.example)")
        print("2. Set JIRA_EMAIL, JIRA_API_TOKEN, and JIRA_BASE_URL")
        return None
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return None


async def test_update_ticket(issue_key: str = "SCRUM-6"):
    """Test updating a Jira ticket by adding a comment"""
    print("\n" + "="*60)
    print("TEST 2: UPDATE TICKET (ADD COMMENT)")
    print("="*60)
    
    # Sample payload for updating a ticket
    update_payload: JiraAgentState = {
        "action": "update_ticket",
        "summary": "Updated summary for testing",
        "issueKey": issue_key,
        "description": "Development update:\n\n✓ OAuth2 integration completed\n✓ Google login working\n✓ GitHub login working\n⏳ Session management in progress\n\nEstimated completion: 2 days"
    }
    
    try:
        print(f"\n💬 Adding comment to ticket...")
        print(f"   Issue: {update_payload['issueKey']}")
        print(f"   Comment preview: {update_payload['description'][:50]}...")
        
        # Invoke the jira agent
        result = await jira_agent.ainvoke(update_payload)
        
        print(f"\n✅ SUCCESS!")
        print(f"   Updated Issue: {result.get('issueKey')}")
        
        return True
        
    except ValueError as e:
        print(f"\n❌ Configuration Error: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print(f"\nNote: Make sure the issue key '{issue_key}' exists in your Jira project")
        return False


async def main():
    """Main entry point to test Jira agent"""
    print("\n" + "="*60)
    print("JIRA AGENT TEST SUITE")
    print("="*60)
    
    # Example test: call with unified sample payload
    print("\n--- Testing with sample_payload ---")
    await main_with_payload(sample_payload)

# New entry point for orchestrator agent
async def main_with_payload(payload: JiraAgentState):
    """Entry point for orchestrator agent to call Jira agent with payload"""
    # Decide action based on presence of 'issueKey'
    if payload.get("action") == "update_ticket" or "issueKey" in payload:
        await test_update_ticket_with_payload(payload)
    else:
        await test_create_ticket_with_payload(payload)

# Helper functions to use the orchestrator's payload
async def test_create_ticket_with_payload(payload: JiraAgentState):
    print("\n📝 Creating ticket (from orchestrator payload)...")
    try:
        result = await jira_agent.ainvoke(payload)
        print(f"\n✅ SUCCESS! Created Issue: {result.get('issueKey')}")
        return result.get('issueKey')
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return None

async def test_update_ticket_with_payload(payload: JiraAgentState):
    print("\n💬 Updating ticket (from orchestrator payload)...")
    try:
        result = await jira_agent.ainvoke(payload)
        print(f"\n✅ SUCCESS! Updated Issue: {result.get('issueKey')}")
        return True
    except Exception as e:
        print(f"\n❌ Error: {e}")
    
    print("\n" + "="*60)
    print("TEST SUITE COMPLETED")
    print("="*60 + "\n")
    return False


if __name__ == "__main__":
    asyncio.run(main())
