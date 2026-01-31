#!/usr/bin/env python3
"""Inspect Vector Database Contents"""

import pickle
import faiss
from pathlib import Path
from pprint import pprint
import json

def inspect_vector_store():
    """Inspect and display vector store contents"""
    
    # Paths
    vector_store_path = Path("./data/vector_store")
    index_path = vector_store_path / "jira_tickets.index"
    metadata_path = vector_store_path / "jira_tickets_metadata.pkl"
    
    print("=" * 80)
    print("🔍 JIRA VECTOR DATABASE INSPECTOR")
    print("=" * 80)
    print()
    
    # Check if files exist
    if not index_path.exists():
        print("❌ FAISS index not found!")
        print(f"   Expected: {index_path}")
        print("\n💡 Run the server first to sync tickets:")
        print("   python main.py")
        return
    
    if not metadata_path.exists():
        print("❌ Metadata file not found!")
        print(f"   Expected: {metadata_path}")
        return
    
    # Load FAISS index
    print("📊 FAISS Index Information:")
    print("-" * 80)
    try:
        index = faiss.read_index(str(index_path))
        print(f"✅ Index Type: {type(index).__name__}")
        print(f"✅ Total Vectors: {index.ntotal}")
        print(f"✅ Vector Dimension: {index.d}")
        print(f"✅ Is Trained: {index.is_trained}")
        print()
    except Exception as e:
        print(f"❌ Error reading index: {e}")
        return
    
    # Load metadata
    print("📋 Ticket Metadata:")
    print("-" * 80)
    try:
        with open(metadata_path, 'rb') as f:
            metadata = pickle.load(f)
        
        print(f"✅ Total Tickets: {len(metadata)}")
        print()
        
        if not metadata:
            print("⚠️  No tickets in database yet!")
            return
        
        # Summary statistics
        print("📈 Summary Statistics:")
        print("-" * 80)
        
        # Count by status
        status_counts = {}
        priority_counts = {}
        type_counts = {}
        
        for ticket in metadata:
            status = ticket.get('status', 'Unknown')
            priority = ticket.get('priority', 'Unknown')
            issue_type = ticket.get('issue_type', 'Unknown')
            
            status_counts[status] = status_counts.get(status, 0) + 1
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
            type_counts[issue_type] = type_counts.get(issue_type, 0) + 1
        
        print(f"📊 By Status:")
        for status, count in sorted(status_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"   {status}: {count}")
        
        print(f"\n🎯 By Priority:")
        for priority, count in sorted(priority_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"   {priority}: {count}")
        
        print(f"\n🏷️  By Type:")
        for itype, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"   {itype}: {count}")
        
        print()
        
        # Show sample tickets
        print("📝 Sample Tickets (First 5):")
        print("=" * 80)
        
        for i, ticket in enumerate(metadata[:5], 1):
            print(f"\n{i}. {ticket['key']} - {ticket['status']}")
            print(f"   Summary: {ticket['summary']}")
            print(f"   Priority: {ticket['priority']} | Type: {ticket['issue_type']}")
            print(f"   Created: {ticket['created'][:10]}")
            if ticket.get('description'):
                desc = ticket['description'][:100] + "..." if len(ticket['description']) > 100 else ticket['description']
                print(f"   Description: {desc}")
        
        print()
        print("=" * 80)
        
        # Export options
        print("\n💾 Export Options:")
        print("-" * 80)
        
        export_choice = input("\n📤 Export all tickets to JSON? (y/n): ").strip().lower()
        
        if export_choice == 'y':
            export_path = "vector_db_export.json"
            with open(export_path, 'w') as f:
                json.dump(metadata, f, indent=2, default=str)
            print(f"✅ Exported to: {export_path}")
        
        # Search simulation
        print("\n" + "=" * 80)
        search_choice = input("\n🔍 Want to simulate a search? (y/n): ").strip().lower()
        
        if search_choice == 'y':
            query = input("Enter search query: ").strip()
            if query:
                simulate_search(query, metadata)
        
    except Exception as e:
        print(f"❌ Error reading metadata: {e}")
        import traceback
        traceback.print_exc()


def simulate_search(query: str, metadata: list):
    """Simulate a search (keyword-based for demo)"""
    print("\n🔍 Search Results (keyword-based demo):")
    print("-" * 80)
    
    query_lower = query.lower()
    results = []
    
    for ticket in metadata:
        summary = ticket.get('summary', '').lower()
        description = ticket.get('description', '').lower()
        
        if query_lower in summary or query_lower in description:
            results.append(ticket)
    
    if results:
        print(f"Found {len(results)} matching ticket(s):\n")
        for i, ticket in enumerate(results[:10], 1):
            print(f"{i}. {ticket['key']}: {ticket['summary']}")
            print(f"   Status: {ticket['status']} | Priority: {ticket['priority']}")
            print()
    else:
        print("No matching tickets found.")


def show_detailed_ticket():
    """Show detailed view of a specific ticket"""
    metadata_path = Path("./data/vector_store/jira_tickets_metadata.pkl")
    
    if not metadata_path.exists():
        print("❌ Metadata file not found!")
        return
    
    with open(metadata_path, 'rb') as f:
        metadata = pickle.load(f)
    
    ticket_key = input("\nEnter ticket key (e.g., SCRUM-123): ").strip().upper()
    
    for ticket in metadata:
        if ticket['key'] == ticket_key:
            print("\n" + "=" * 80)
            print(f"📋 Ticket Details: {ticket_key}")
            print("=" * 80)
            pprint(ticket)
            return
    
    print(f"❌ Ticket {ticket_key} not found in database.")


if __name__ == "__main__":
    try:
        inspect_vector_store()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

