"""Example usage of Jira Assistant"""

import asyncio
from src.graphs import run_jira_assistant


async def main():
    """Example usage of the Jira assistant"""
    
    print("=" * 60)
    print("Jira Assistant - Example Usage")
    print("=" * 60)
    
    # Example 1: Search for tickets
    print("\n1. Searching for tickets about login issues...")
    result = await run_jira_assistant("Find tickets about login issues")
    print(f"\nResponse: {result['response']}")
    print(f"Intent: {result['intent']}")
    print(f"Similar tickets found: {len(result['similar_tickets'])}")
    
    # Example 2: Create a new ticket
    print("\n" + "=" * 60)
    print("\n2. Creating a new ticket...")
    result = await run_jira_assistant(
        "Create a bug ticket: Users unable to reset password, getting 500 error"
    )
    print(f"\nResponse: {result['response']}")
    print(f"Intent: {result['intent']}")
    if result['created_ticket']:
        print(f"Created ticket: {result['created_ticket']['key']}")
    
    # Example 3: General question
    print("\n" + "=" * 60)
    print("\n3. Asking general question...")
    result = await run_jira_assistant("How can you help me?")
    print(f"\nResponse: {result['response']}")
    print(f"Intent: {result['intent']}")
    
    # Example 4: Update ticket (if you have a ticket key)
    print("\n" + "=" * 60)
    print("\n4. Updating a ticket...")
    result = await run_jira_assistant("Update ticket PROJ-123 priority to High")
    print(f"\nResponse: {result['response']}")
    print(f"Intent: {result['intent']}")
    
    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    # Note: Make sure you have:
    # 1. Configured .env file with your credentials
    # 2. Run the sync job at least once to populate vector store
    # 3. Replace 'PROJ-123' with an actual ticket key from your project
    
    asyncio.run(main())

