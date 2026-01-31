#!/usr/bin/env python3
"""
Validate .env configuration

Run this script to check if your .env file is properly configured
with all required secrets before starting the application.

Usage:
    python validate_env.py
"""

import sys
from pathlib import Path


def validate_env():
    """Validate .env file configuration"""
    
    print("🔍 Validating .env configuration...\n")
    
    # Check if .env exists
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ .env file not found!")
        print("\n📝 To fix this:")
        print("  1. Copy the template:")
        print("     cp .env.example .env")
        print("\n  2. Edit .env and add your secrets:")
        print("     - OPENAI_API_KEY")
        print("     - JIRA_API_TOKEN")
        print("     - JIRA_URL")
        print("     - JIRA_EMAIL")
        print("     - JIRA_PROJECT_KEY")
        return False
    
    print("✅ .env file exists")
    
    # Try to load settings
    try:
        from src.config import settings
        
        print("\n🔑 Checking secrets:")
        
        # Check OpenAI API Key
        if settings.openai_api_key:
            masked_key = settings.openai_api_key[:7] + "..." + settings.openai_api_key[-4:]
            print(f"  ✅ OPENAI_API_KEY: {masked_key}")
        else:
            print("  ❌ OPENAI_API_KEY: Missing")
            return False
        
        # Check Jira credentials
        if settings.jira_url:
            print(f"  ✅ JIRA_URL: {settings.jira_url}")
        else:
            print("  ❌ JIRA_URL: Missing")
            return False
        
        if settings.jira_email:
            print(f"  ✅ JIRA_EMAIL: {settings.jira_email}")
        else:
            print("  ❌ JIRA_EMAIL: Missing")
            return False
        
        if settings.jira_api_token:
            masked_token = settings.jira_api_token[:4] + "..." + settings.jira_api_token[-4:]
            print(f"  ✅ JIRA_API_TOKEN: {masked_token}")
        else:
            print("  ❌ JIRA_API_TOKEN: Missing")
            return False
        
        if settings.jira_project_key:
            print(f"  ✅ JIRA_PROJECT_KEY: {settings.jira_project_key}")
        else:
            print("  ❌ JIRA_PROJECT_KEY: Missing")
            return False
        
        print("\n⚙️  Configuration:")
        print(f"  • OpenAI Model: {settings.openai_model}")
        print(f"  • Embedding Model: {settings.embedding_model}")
        print(f"  • Sync Interval: {settings.sync_interval_hours} hours")
        print(f"  • Sync On Startup: {settings.sync_on_startup}")
        print(f"  • Server Port: {settings.port}")
        print(f"  • Max Similarity Results: {settings.max_similarity_results}")
        print(f"  • Similarity Threshold: {settings.similarity_threshold}")
        
        print("\n✨ Configuration is valid!")
        print("\n🚀 You can now start the application:")
        print("   python main.py")
        
        return True
        
    except ValueError as e:
        print(f"\n❌ Configuration error:\n{e}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = validate_env()
    sys.exit(0 if success else 1)

