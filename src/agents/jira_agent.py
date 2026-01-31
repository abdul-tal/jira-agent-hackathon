"""Jira agent for creating and updating tickets"""

from langchain_openai import ChatOpenAI
from langchain.agents import create_openai_functions_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from loguru import logger

from src.models import AgentState
from src.config import settings
from src.tools.jira_tools import create_jira_ticket_tool, update_jira_ticket_tool, get_jira_ticket_tool


# Initialize LLM
llm = ChatOpenAI(
    model=settings.openai_model,
    temperature=0,
    openai_api_key=settings.openai_api_key
)


JIRA_AGENT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a Jira operations agent. Your role is to create and update Jira tickets based on user requests.

You have access to these tools:
- create_jira_ticket_tool: Create new tickets
- update_jira_ticket_tool: Update existing tickets  
- get_jira_ticket_tool: Get ticket information

When creating tickets:
1. Extract key information from the user's request:
   - Summary: A clear, concise title (10-15 words max)
   - Description: Detailed explanation of the issue or requirement
   - Issue Type: Task, Bug, Story, or Epic (infer from context)
   - Priority: Highest, High, Medium, Low, or Lowest (default: Medium)
   - Labels: Relevant tags (optional)

2. Create well-structured tickets with:
   - Clear, actionable summaries
   - Detailed descriptions with context
   - Appropriate issue type and priority

When updating tickets:
1. Identify the ticket key (e.g., PROJ-123)
2. Determine what needs to be updated
3. Apply the changes using update_jira_ticket_tool

Always confirm the operation success and provide the ticket key in your response."""),
    ("user", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad")
])


# Create agent with tools
tools = [create_jira_ticket_tool, update_jira_ticket_tool, get_jira_ticket_tool]
agent = create_openai_functions_agent(llm, tools, JIRA_AGENT_PROMPT)
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    max_iterations=5,
    return_intermediate_steps=True
)


def jira_node(state: AgentState) -> AgentState:
    """
    Handle Jira ticket operations (create/update)
    
    Args:
        state: Current agent state
    
    Returns:
        Updated state with Jira operation results
    """
    logger.info("Jira agent: Processing ticket operation")
    
    query = state["user_query"]
    intent = state.get("intent", "create")
    
    try:
        # Prepare context
        context_parts = [query]
        
        # If similar tickets were found, include them in context
        if state.get("has_similar_tickets"):
            context_parts.append(
                f"\nNote: Found {len(state['similar_tickets'])} similar tickets. "
                f"Consider if a new ticket is truly needed."
            )
        
        input_text = "\n".join(context_parts)
        
        # Execute agent
        result = agent_executor.invoke({"input": input_text})
        
        # Extract results from intermediate steps
        created_ticket = None
        action_type = intent
        
        for step in result.get("intermediate_steps", []):
            action, observation = step
            if isinstance(observation, dict):
                if observation.get("success") and "ticket" in observation:
                    created_ticket = observation["ticket"]
                    action_type = "create" if "created" in observation.get("message", "").lower() else "update"
        
        state["created_ticket"] = created_ticket
        state["action_type"] = action_type
        state["final_response"] = result["output"]
        
        logger.info(f"Jira agent: Completed {action_type} operation")
        
    except Exception as e:
        logger.error(f"Jira agent error: {e}")
        state["error"] = str(e)
        state["final_response"] = f"I encountered an error while processing your request: {str(e)}"
    
    return state

