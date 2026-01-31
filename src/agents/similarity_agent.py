"""Similarity agent for searching similar tickets"""

from langchain_openai import ChatOpenAI
from langchain.agents import create_openai_functions_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from loguru import logger

from src.models import AgentState
from src.config import settings
from src.tools.vector_search_tools import search_similar_tickets_tool


# Initialize LLM
llm = ChatOpenAI(
    model=settings.openai_model,
    temperature=0,
    openai_api_key=settings.openai_api_key
)


SIMILARITY_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a similarity search agent for Jira tickets. Your role is to find existing tickets similar to the user's query.

Use the search_similar_tickets_tool to search for relevant tickets. Analyze the query and extract key information:
- What is the main topic or issue?
- What are the key technical terms?
- What type of ticket might this be?

When searching:
1. Use descriptive search terms based on the query
2. Look for tickets with similar problems, features, or topics
3. Return the most relevant matches

After searching, summarize what you found clearly."""),
    ("user", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad")
])


# Create agent
tools = [search_similar_tickets_tool]
agent = create_openai_functions_agent(llm, tools, SIMILARITY_PROMPT)
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    max_iterations=3,
    return_intermediate_steps=False
)


def similarity_node(state: AgentState) -> AgentState:
    """
    Search for similar tickets using vector search
    
    Args:
        state: Current agent state
    
    Returns:
        Updated state with similar tickets
    """
    logger.info("Similarity agent: Searching for similar tickets")
    
    query = state["user_query"]
    
    try:
        # Use agent to search
        result = agent_executor.invoke({"input": query})
        
        # Parse the tool output to extract similar tickets
        # The agent will have called search_similar_tickets_tool
        # We need to extract the actual tickets from the intermediate steps
        
        # For now, call the tool directly to get structured results
        from src.tools.vector_search_tools import search_similar_tickets_tool as search_tool
        search_result = search_tool.invoke({"query": query, "max_results": settings.max_similarity_results})
        
        if search_result["success"] and search_result["similar_tickets"]:
            state["similar_tickets"] = search_result["similar_tickets"]
            state["has_similar_tickets"] = True
            logger.info(f"Found {len(search_result['similar_tickets'])} similar tickets")
        else:
            state["similar_tickets"] = []
            state["has_similar_tickets"] = False
            logger.info("No similar tickets found")
        
    except Exception as e:
        logger.error(f"Similarity agent error: {e}")
        state["similar_tickets"] = []
        state["has_similar_tickets"] = False
        state["error"] = str(e)
    
    return state

