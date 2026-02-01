#!/usr/bin/env python3
"""Test if OpenAI API key in .env works with the project's LLM models."""

import sys
import os


def test_key(key: str) -> bool:
    """Test key with gpt-4o-mini (guardrail model)."""
    try:
        from openai import OpenAI
        client = OpenAI(api_key=key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Say OK"}],
            max_tokens=5
        )
        return bool(response.choices and response.choices[0].message.content)
    except Exception:
        return False


def main():
    # Load from .env
    from dotenv import load_dotenv
    load_dotenv()
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        print("❌ OPENAI_API_KEY not found in .env")
        return False
    print("Testing API key from .env...")
    if test_key(key):
        print("✅ API key works with gpt-4o-mini")
        return True
    print("❌ API key invalid or expired")
    return False


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
