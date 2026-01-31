#!/usr/bin/env python3
"""Test the streaming chat endpoint"""

import requests
import json

API_URL = "http://localhost:8000"

def test_streaming():
    """Test the /chat/stream endpoint"""
    url = f"{API_URL}/chat/stream"
    payload = {
        "session_id": "test-session-123",
        "question": "find tickets about jira testing"
    }
    
    print("🚀 Testing streaming endpoint...")
    print(f"URL: {url}")
    print(f"Payload: {payload}\n")
    
    try:
        with requests.post(url, json=payload, stream=True, timeout=60) as response:
            if response.status_code != 200:
                print(f"❌ Error: HTTP {response.status_code}")
                return
            
            print("✅ Connected! Receiving events:\n")
            print("-" * 60)
            
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        try:
                            event_data = json.loads(line[6:])
                            event_type = event_data.get('event', '')
                            message = event_data.get('message', '')
                            timestamp = event_data.get('timestamp', '')
                            
                            # Print event
                            print(f"[{timestamp}] {event_type.upper()}: {message}")
                            
                            if event_type == 'complete':
                                result = event_data.get('result', {})
                                print(f"\n📊 Final Result:")
                                print(f"   Session ID: {result.get('session_id', '')}")
                                print(f"   Type: {result.get('type', '')}")
                                print(f"   Message: {result.get('message', '')}")
                                print(f"   Tickets: {len(result.get('tickets', []))}")
                                if result.get('tickets'):
                                    for ticket in result['tickets']:
                                        score_text = f" (Score: {ticket.get('similarity_score', 0):.3f})" if ticket.get('similarity_score') else ""
                                        print(f"      - {ticket['key']}: {ticket['summary']}{score_text}")
                                        
                        except json.JSONDecodeError as e:
                            print(f"⚠️  JSON decode error: {e}")
            
            print("-" * 60)
            print("\n✅ Stream completed successfully!")
            
    except requests.exceptions.Timeout:
        print("❌ Request timeout")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    test_streaming()

