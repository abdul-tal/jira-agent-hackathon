import os
import asyncio
from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Import the compiled Jira agent graph
from graph.jira_graph import jira_agent

# Import sample payload
try:
    from sample_payload import sample_payload
except Exception:
    sample_payload = {}

app = FastAPI(title="Jira Agent API")


class PayloadModel(BaseModel):
    payload: Dict[str, Any]


@app.get("/sample")
async def get_sample():
    """Return a sample payload. Uncomment issueKey for update."""
    return {"sample_payload": sample_payload}


@app.post("/jira")
async def call_jira_agent(payload: Dict[str, Any]):
    """Endpoint to accept a Jira payload and invoke the Jira agent graph.

    The endpoint will set 'action' based on the presence of 'issueKey' if not provided.
    Returns the final state (including issueKey on create) and a friendly response.
    """
    # Ensure payload is a dict
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Payload must be a JSON object")

    # Decide action on behalf of orchestrator if missing
    if not payload.get("action"):
        if payload.get("issueKey"):
            payload["action"] = "update_ticket"
        else:
            payload["action"] = "create_ticket"

    # Minimal validation
    if payload["action"] == "create_ticket":
        if not payload.get("projectKey") or not payload.get("summary"):
            raise HTTPException(status_code=400, detail="Missing required fields for create_ticket: projectKey and summary")
    elif payload["action"] == "update_ticket":
        if not payload.get("issueKey"):
            raise HTTPException(status_code=400, detail="Missing required field for update_ticket: issueKey")

    # Invoke the Jira agent graph
    try:
        result = await jira_agent.ainvoke(payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Build friendly response
    issue_key = result.get("issueKey") or result.get("issue_key")
    base_url = os.getenv("JIRA_BASE_URL")
    issue_url = f"{base_url}/browse/{issue_key}" if base_url and issue_key else None

    return {
        "success": True,
        "action": payload["action"],
        "result_state": result,
        "issue_key": issue_key,
        "issue_url": issue_url,
    }
