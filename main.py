"""Main entry point for Jira Assistant"""

import sys
import uvicorn
from loguru import logger

from src.config import settings


# Configure logger
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level=settings.log_level
)
logger.add(
    "logs/jira_assistant.log",
    rotation="500 MB",
    retention="10 days",
    level=settings.log_level
)


def main():
    """Start the FastAPI server"""
    logger.info("Starting Jira Assistant...")
    logger.info(f"Configuration: {settings.jira_url} | Project: {settings.jira_project_key}")
    
    uvicorn.run(
        "src.api.main:app",
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower(),
        reload=False
    )


if __name__ == "__main__":
    main()

