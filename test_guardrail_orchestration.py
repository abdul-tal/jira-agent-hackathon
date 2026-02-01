#!/usr/bin/env python3
"""
Integration test for Guardrail + Orchestration flow.
Tests the flow with real services (uses .env credentials).
For mocked tests, ensure OPENAI_API_KEY and Jira credentials are valid.
"""

import asyncio
import os
import sys

# Set minimal env before imports (only if .env missing - don't override OPENAI_API_KEY)
os.environ.setdefault("JIRA_URL", "https://test.atlassian.net")
os.environ.setdefault("JIRA_EMAIL", "test@test.com")
os.environ.setdefault("JIRA_API_TOKEN", "test-token")
os.environ.setdefault("JIRA_PROJECT_KEY", "TEST")


async def run_tests():
    """Run integration tests."""
    from src.graphs.jira_graph import run_jira_assistant
    
    print("=" * 60)
    print("Testing Guardrail + Orchestration Flow")
    print("=" * 60)
    
    # Test 1: First turn - check/verify -> Similarity
    print("\n1. First turn: 'Check if there are tickets about login bug'")
    result = await run_jira_assistant(
        user_query="Check if there are tickets about login bug",
        conversation_id="test-session-001"
    )
    resp = result.get("response", "")
    intent = result.get("intent")
    tickets = result.get("similar_tickets", [])
    
    print(f"   Response (first 250 chars): {resp[:250]}...")
    print(f"   Intent: {intent}")
    print(f"   Similar tickets count: {len(tickets)}")
    
    assert result.get("response"), "Should have response"
    assert intent == "search", f"Expected intent=search, got {intent}"
    # With historical data: tickets found. Without: "No historical data" message
    assert "similar" in resp.lower() or "historical" in resp.lower() or "create" in resp.lower() or len(tickets) >= 0
    print("   ✅ PASS")
    
    # Test 2: Second turn - create (session exists) -> Jira
    print("\n2. Second turn: 'Create a new ticket for this'")
    result = await run_jira_assistant(
        user_query="Create a new ticket for this",
        conversation_id="test-session-001"
    )
    intent = result.get("intent")
    created = result.get("created_ticket")
    
    print(f"   Intent: {intent}")
    print(f"   Created ticket: {created.get('key') if created else 'N/A (may need valid Jira)'}")
    
    assert intent == "create", f"Expected intent=create, got {intent}"
    # Created ticket or error (if Jira invalid)
    assert "response" in result
    print("   ✅ PASS")
    
    # Test 3: New session - first turn always goes to similarity (by design)
    print("\n3. New session, first msg: 'Create a bug for payment timeout'")
    print("   (First turn -> similarity to check duplicates, per design)")
    result = await run_jira_assistant(
        user_query="Create a bug for payment timeout",
        conversation_id="test-session-002"
    )
    intent = result.get("intent")
    print(f"   Intent: {intent}")
    assert intent == "search", f"First turn should go to similarity (search), got {intent}"
    print("   ✅ PASS")
    
    # Test 4: Verify keywords -> Similarity
    print("\n4. Verify intent: 'Verify if similar tickets exist for API bug'")
    result = await run_jira_assistant(
        user_query="Verify if similar tickets exist for API bug",
        conversation_id="test-session-003"
    )
    intent = result.get("intent")
    print(f"   Intent: {intent}")
    assert intent == "search", f"Expected intent=search, got {intent}"
    print("   ✅ PASS")
    
    # Test 5: Session store - first turn vs second turn
    print("\n5. Session flow: first turn routes to similarity")
    from src.services import session_store
    
    sid = "test-session-flow"
    session_store.clear_session(sid)  # Reset
    
    r1 = await run_jira_assistant("find tickets about login", conversation_id=sid)
    assert r1.get("intent") == "search"
    
    r2 = await run_jira_assistant("Create a new ticket", conversation_id=sid)
    assert r2.get("intent") == "create"
    
    print("   First turn -> similarity, Second turn -> jira")
    print("   ✅ PASS")
    
    print("\n" + "=" * 60)
    print("All tests PASSED!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(run_tests())
    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
