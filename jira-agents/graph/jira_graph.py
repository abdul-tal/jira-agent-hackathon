# create a langgraph stategraph for jira agent
# this graph should route to create or update node based on action

from typing import Literal
from langgraph.graph import StateGraph, END
import sys
import os

# Add parent directory to path to import agents
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.jira_agents import (
    JiraAgentState,
    execute_create_ticket_action,
    execute_update_ticket_action
)


# Node functions
async def create_ticket_node(state: JiraAgentState) -> JiraAgentState:
    """
    Node to handle ticket creation
    
    Args:
        state: Current state with ticket creation details
        
    Returns:
        Updated state with created issue key
    """
    print(f"Creating ticket: {state.get('summary')}")
    
    issue_key = await execute_create_ticket_action(state)
    
    # Update state with the created issue key
    state["issueKey"] = issue_key
    print(f"✓ Created ticket: {issue_key}")
    
    return state


async def update_ticket_node(state: JiraAgentState) -> JiraAgentState:
    """
    Node to handle ticket updates (add comment)
    
    Args:
        state: Current state with update details
        
    Returns:
        Updated state after adding comment
    """
    print(f"Updating ticket: {state.get('issueKey')}")
    
    success = await execute_update_ticket_action(state)
    
    if success:
        print(f"✓ Updated ticket: {state.get('issueKey')}")
    
    return state


# Routing function
def route_action(state: JiraAgentState) -> str:
    """
    Router function that returns action from state
    
    Args:
        state: Current state with action field
        
    Returns:
        str: The action value from state (e.g., "create_ticket", "update_ticket")
    """
    return state.get("action", "")


# Build the StateGraph
def create_jira_graph() -> StateGraph:
    """
    Create a LangGraph StateGraph for Jira agent
    
    The graph routes to create or update node based on action field:
    - START -> router -> create_ticket -> END
    - START -> router -> update_ticket -> END
    
    Returns:
        Compiled StateGraph
    """
    # Initialize the graph
    workflow = StateGraph(JiraAgentState)
    
    # Add nodes
    workflow.add_node("create_ticket", create_ticket_node)
    workflow.add_node("update_ticket", update_ticket_node)
    
    # Set entry point with conditional routing
    workflow.set_conditional_entry_point(
        route_action,
        {
            "create_ticket": "create_ticket",
            "update_ticket": "update_ticket"
        }
    )
    
    # Add edges to END
    workflow.add_edge("create_ticket", END)
    workflow.add_edge("update_ticket", END)
    
    # Compile the graph
    return workflow.compile()


# Compile Jira agent graph and expose as jira_agent variable
jira_agent = create_jira_graph()


# Legacy alias for backward compatibility
jira_graph = jira_agent


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def test_agent():
        """Test the Jira agent with sample actions"""
        
        # Test 1: Create ticket
        print("\n=== Test 1: Create Ticket ===")
        create_state: JiraAgentState = {
            "action": "create_ticket",
            "projectKey": "PROJ",
            "summary": "Test ticket from graph",
            "description": "This ticket was created via LangGraph",
            "issueType": "Task"
        }
        
        try:
            result = await jira_agent.ainvoke(create_state)
            print(f"Final state: {result}")
        except Exception as e:
            print(f"Error: {e}")
        
        # Test 2: Update ticket (add comment)
        print("\n=== Test 2: Update Ticket ===")
        update_state: JiraAgentState = {
            "action": "update_ticket",
            "issueKey": "PROJ-123",
            "description": "This comment was added via LangGraph"
        }
        
        try:
            result = await jira_agent.ainvoke(update_state)
            print(f"Final state: {result}")
        except Exception as e:
            print(f"Error: {e}")
    
    # Uncomment to test
    # asyncio.run(test_agent())
    print("Jira agent compiled and ready. Uncomment asyncio.run() to test.")
