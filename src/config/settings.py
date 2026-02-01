"""Configuration settings for Jira Assistant

All sensitive credentials are loaded from .env file.
Create a .env file in the project root with your secrets:

    OPENAI_API_KEY=sk-proj-...
    JIRA_API_TOKEN=...
    JIRA_URL=https://...
    etc.

See .env.example for a complete template.
"""

from typing import Optional
from pydantic import field_validator, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
import os


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    Pydantic automatically reads from .env file and validates all settings.
    Required secrets (API keys, tokens) must be provided in .env file.
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # OpenAI Configuration - REQUIRED (from .env: OPENAI_API_KEY)
    openai_api_key: str = Field(
        ...,
        description="OpenAI API key - get from https://platform.openai.com/api-keys"
    )
    openai_model: str = "gpt-4-turbo-preview"
    embedding_model: str = "text-embedding-3-small"
    
    # Jira Configuration - REQUIRED (from .env)
    jira_url: str = Field(
        ...,
        description="Jira instance URL (e.g., https://company.atlassian.net)"
    )
    jira_email: str = Field(
        ...,
        description="Jira account email"
    )
    jira_api_token: str = Field(
        ...,
        description="Jira API token - get from https://id.atlassian.com/manage-profile/security/api-tokens"
    )
    jira_project_key: str = Field(
        ...,
        description="Jira project key (e.g., PROJ)"
    )
    
    @field_validator('openai_api_key')
    @classmethod
    def validate_openai_key(cls, v: str) -> str:
        """Validate OpenAI API key is not empty"""
        if not v or not v.strip():
            raise ValueError(
                "OPENAI_API_KEY is required. "
                "Get your key from https://platform.openai.com/api-keys "
                "and add it to .env file"
            )
        if not v.startswith('sk-'):
            raise ValueError(
                "OPENAI_API_KEY should start with 'sk-'. "
                "Please check your API key."
            )
        return v.strip()
    
    @field_validator('jira_api_token')
    @classmethod
    def validate_jira_token(cls, v: str) -> str:
        """Validate Jira API token is not empty"""
        if not v or not v.strip():
            raise ValueError(
                "JIRA_API_TOKEN is required. "
                "Get your token from https://id.atlassian.com/manage-profile/security/api-tokens "
                "and add it to .env file"
            )
        return v.strip()
    
    @field_validator('jira_url')
    @classmethod
    def validate_jira_url(cls, v: str) -> str:
        """Validate and clean Jira URL"""
        if not v or not v.strip():
            raise ValueError("JIRA_URL is required in .env file")
        # Remove trailing slash if present
        return v.strip().rstrip('/')
    
    @field_validator('jira_project_key')
    @classmethod
    def validate_project_key(cls, v: str) -> str:
        """Validate Jira project key"""
        if not v or not v.strip():
            raise ValueError("JIRA_PROJECT_KEY is required in .env file")
        return v.strip().upper()
    
    # Vector Store Configuration
    vector_store_path: Path = Field(
        default=Path("./data/vector_store"),
        description="Path to FAISS vector store directory"
    )
    faiss_index_name: str = Field(
        default="jira_tickets",
        description="Name of FAISS index file"
    )
    
    # Sync Job Configuration
    sync_interval_hours: int = Field(
        default=24,
        description="Hours between ticket sync jobs",
        ge=1
    )
    sync_on_startup: bool = Field(
        default=True,
        description="Run ticket sync when server starts"
    )
    
    # Server Configuration
    host: str = Field(
        default="0.0.0.0",
        description="Server host address"
    )
    port: int = Field(
        default=8000,
        description="Server port number",
        ge=1,
        le=65535
    )
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR)"
    )
    
    # Agent Configuration
    max_similarity_results: int = Field(
        default=5,
        description="Maximum number of similar tickets to return",
        ge=1,
        le=20
    )
    similarity_threshold: float = Field(
        default=0.5,
        description="Minimum similarity score for matches (0.0-1.0, 0.5 = 50% match minimum)",
        ge=0.0,
        le=1.0
    )
    max_retries: int = Field(
        default=3,
        description="Maximum retry attempts for API calls",
        ge=1,
        le=10
    )
    
    # LangSmith Configuration (Optional - for tracing/debugging)
    langchain_tracing_v2: bool = Field(
        default=False,
        description="Enable LangSmith tracing for debugging"
    )
    langchain_api_key: Optional[str] = Field(
        default=None,
        description="LangSmith API key - get from https://smith.langchain.com/"
    )
    langchain_project: str = Field(
        default="jira-assistant",
        description="LangSmith project name"
    )
    langchain_endpoint: str = Field(
        default="https://api.smith.langchain.com",
        description="LangSmith API endpoint"
    )
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Ensure vector store directory exists
        self.vector_store_path.mkdir(parents=True, exist_ok=True)
        
        # Configure LangSmith tracing if enabled
        if self.langchain_tracing_v2 and self.langchain_api_key:
            os.environ["LANGCHAIN_TRACING_V2"] = "true"
            os.environ["LANGCHAIN_API_KEY"] = self.langchain_api_key
            os.environ["LANGCHAIN_PROJECT"] = self.langchain_project
            os.environ["LANGCHAIN_ENDPOINT"] = self.langchain_endpoint
            # Don't log the full API key for security
            key_preview = self.langchain_api_key[:15] + "..." if len(self.langchain_api_key) > 15 else "***"
            print(f"✅ LangSmith tracing enabled for project: {self.langchain_project} (key: {key_preview})")
        else:
            # Explicitly disable if not configured
            os.environ["LANGCHAIN_TRACING_V2"] = "false"


def load_settings() -> Settings:
    """
    Load settings from .env file.
    
    Raises helpful error messages if required secrets are missing.
    
    Returns:
        Settings instance with all configuration loaded
    
    Raises:
        ValueError: If required secrets are missing or invalid
        FileNotFoundError: If .env file doesn't exist (with helpful message)
    """
    env_file = Path(".env")
    
    if not env_file.exists():
        raise FileNotFoundError(
            f"\n\n❌ .env file not found!\n\n"
            f"Please create a .env file in the project root:\n"
            f"  1. Copy the template: cp .env.example .env\n"
            f"  2. Edit .env with your credentials\n"
            f"  3. Required secrets:\n"
            f"     - OPENAI_API_KEY (from https://platform.openai.com/api-keys)\n"
            f"     - JIRA_API_TOKEN (from https://id.atlassian.com/manage-profile/security/api-tokens)\n"
            f"     - JIRA_URL, JIRA_EMAIL, JIRA_PROJECT_KEY\n\n"
            f"See .env.example for a complete template.\n"
        )
    
    try:
        return Settings()
    except Exception as e:
        raise ValueError(
            f"\n\n❌ Error loading settings from .env file:\n\n"
            f"{str(e)}\n\n"
            f"Please check your .env file and ensure all required secrets are set.\n"
            f"See .env.example for the correct format.\n"
        ) from e


# Global settings instance
# This will raise an error with helpful message if .env is missing or invalid
settings = load_settings()

