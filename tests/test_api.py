"""Tests for API endpoints"""

import pytest
from fastapi.testclient import TestClient

from src.api.main import app


client = TestClient(app)


def test_root_endpoint():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Jira Assistant API"
    assert data["version"] == "1.0.0"


def test_health_endpoint():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "jira-assistant"


def test_chat_empty_query():
    """Test chat endpoint with empty query"""
    response = client.post("/chat", json={"session_id": "test", "question": ""})
    assert response.status_code == 400


def test_stats_endpoint():
    """Test stats endpoint"""
    response = client.get("/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_tickets" in data
    assert "dimension" in data

