"""Example usage of the Similarity Agent

This script demonstrates how to use the Similarity Agent to search for
existing Jira tickets based on user queries.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from similarity_agent.agent import SimilarityAgent
from loguru import logger


def main():
    """Run example searches using the Similarity Agent."""
    
    # Initialize the agent
    logger.info("Initializing Similarity Agent...")
    agent = SimilarityAgent()
    
    # Print graph structure
    print(agent.get_graph_visualization())
    print("\n" + "="*80 + "\n")
    
    # Example queries
    example_queries = [
        "User authentication issue in login page",
        "Need to implement dark mode for dashboard",
        "Database connection timeout errors",
        "Add export functionality to reports",
        "Fix broken links in navigation menu"
    ]
    
    print("Running example searches...\n")
    print("NOTE: The agent will return matched Jira tickets with full details.\n")
    
    for i, query in enumerate(example_queries, 1):
        print(f"\n{'='*80}")
        print(f"Example {i}: {query}")
        print('='*80)
        
        # Search for similar tickets
        result = agent.search(query=query, max_results=3)
        
        # Display results
        print(f"\n{result['message']}")
        
        if result['has_matches']:
            print(f"\n📊 Search Summary:")
            print(f"  - Confidence Level: {result['confidence_level'].upper()}")
            print(f"  - Total Matches: {result['total_matches']}")
            
            print(f"\n📋 Returned Tickets:")
            for ticket in result['matched_tickets']:
                print(f"  • {ticket['key']}: {ticket['summary'][:60]}...")
                print(f"    Similarity: {ticket['similarity_score']:.1%} | Status: {ticket['status']}")
            
            if result['best_match']:
                best = result['best_match']
                print(f"\n⭐ Best Match Ticket:")
                print(f"  Key: {best['key']}")
                print(f"  Similarity: {best['similarity_score']:.1%}")
                print(f"  Summary: {best['summary']}")
                if best.get('match_reason'):
                    print(f"  Why: {best['match_reason']}")
        
        print("\n")
    
    print("\n" + "="*80)
    print("Example complete!")
    print("All matched tickets were returned with full details (key, summary, description, type, priority, status, labels).")


def interactive_mode():
    """Run the agent in interactive mode."""
    
    logger.info("Starting Similarity Agent in interactive mode...")
    agent = SimilarityAgent()
    
    print("\n" + "="*80)
    print("SIMILARITY AGENT - Interactive Mode")
    print("="*80)
    print(agent.get_graph_visualization())
    print("\n🔍 Search for similar Jira tickets using natural language queries.")
    print("The agent will return matched tickets with full details.\n")
    print("Enter your queries to search for similar tickets.")
    print("Type 'quit' or 'exit' to stop.\n")
    
    while True:
        try:
            query = input("🔎 Query: ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                print("\nGoodbye!")
                break
            
            if not query:
                continue
            
            print("\n⏳ Searching for similar tickets...\n")
            result = agent.search(query=query, max_results=5)
            
            # Display the formatted response
            print(result['message'])
            
            # Show quick summary
            if result['has_matches']:
                print(f"\n✅ Returned {result['total_matches']} matched ticket(s) with full details")
                print(f"   Confidence: {result['confidence_level'].upper()}")
            else:
                print(f"\n❌ No matched tickets found")
            
            print("\n" + "-"*80 + "\n")
            
        except KeyboardInterrupt:
            print("\n\nInterrupted. Goodbye!")
            break
        except Exception as e:
            logger.error(f"Error: {e}")
            print(f"\n❌ Error: {e}\n")


if __name__ == "__main__":
    # Run in interactive mode if no arguments, otherwise run examples
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        interactive_mode()
    else:
        main()

