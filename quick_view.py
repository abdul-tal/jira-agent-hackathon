"""Quick view of vector database contents"""

import pickle
import json
from pathlib import Path

# Load metadata
metadata_path = Path("./data/vector_store/jira_tickets_metadata.pkl")

if metadata_path.exists():
    with open(metadata_path, 'rb') as f:
        tickets = pickle.load(f)
    
    print(f"📊 Total tickets in vector DB: {len(tickets)}\n")
    
    # Show first 3 tickets
    for i, ticket in enumerate(tickets[:3], 1):
        print(f"{i}. {ticket['key']}: {ticket['summary']}")
        print(f"   Status: {ticket['status']} | Priority: {ticket['priority']}")
        print(f"   Description: {ticket['description'][:80]}...")
        print()
    
    # Export to JSON for easy viewing
    with open('tickets_export.json', 'w') as f:
        json.dump(tickets, f, indent=2, default=str)
    
    print(f"✅ Full export saved to: tickets_export.json")
    print(f"📝 You can open it with any text editor")
else:
    print("❌ No vector store found. Run 'python main.py' first to sync tickets.")

