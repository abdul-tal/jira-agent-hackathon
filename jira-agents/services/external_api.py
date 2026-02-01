import os
import asyncio
import logging
from typing import Any, Dict, Optional

import httpx

logger = logging.getLogger(__name__)

# Read default endpoint and headers from environment
DEFAULT_NOTIFICATION_ENDPOINT = os.getenv("NOTIFICATION_ENDPOINT")
DEFAULT_NOTIFICATION_API_KEY = os.getenv("NOTIFICATION_API_KEY")


async def post_notification(
    payload: Dict[str, Any],
    endpoint: Optional[str] = None,
    headers: Optional[Dict[str, str]] = None,
    retries: int = 3,
    timeout: float = 10.0,
    backoff_factor: float = 0.5,
) -> Dict[str, Any]:
    """Post a JSON payload to a configured endpoint with retries and error handling.

    Args:
        payload: JSON-serializable dict to send
        endpoint: URL to post to; if None, DEFAULT_NOTIFICATION_ENDPOINT is used
        headers: Optional headers to include; if None and DEFAULT_NOTIFICATION_API_KEY is set,
                 Authorization: Bearer <API_KEY> will be used
        retries: Number of retry attempts for transient errors
        timeout: Request timeout in seconds
        backoff_factor: Base backoff multiplier for exponential backoff

    Returns:
        Dict with result information: {"success": bool, "status_code": int|None, "response": Any|None, "error": str|None}
    """
    endpoint = endpoint or DEFAULT_NOTIFICATION_ENDPOINT
    if not endpoint:
        msg = "No notification endpoint configured (NOTIFICATION_ENDPOINT not set). Skipping notification."
        logger.info(msg)
        return {"success": False, "status_code": None, "response": None, "error": msg}

    # Prepare headers
    headers = headers.copy() if headers else {}
    if DEFAULT_NOTIFICATION_API_KEY and "Authorization" not in headers:
        headers["Authorization"] = f"Bearer {DEFAULT_NOTIFICATION_API_KEY}"
    headers.setdefault("Content-Type", "application/json")
    headers.setdefault("Accept", "application/json")

    attempt = 0
    while True:
        attempt += 1
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(endpoint, json=payload, headers=headers)

            status = response.status_code
            text = None
            try:
                text = response.json()
            except Exception:
                text = response.text

            if 200 <= status < 300:
                logger.info(f"Notification sent successfully to {endpoint} (status={status})")
                return {"success": True, "status_code": status, "response": text, "error": None}

            # Retry on server errors or 429 (rate limit)
            if status >= 500 or status == 429:
                if attempt <= retries:
                    wait = backoff_factor * (2 ** (attempt - 1))
                    logger.warning(
                        f"Transient error posting notification (status {status}). Retrying in {wait}s... (attempt {attempt}/{retries})"
                    )
                    await asyncio.sleep(wait)
                    continue
                else:
                    err = f"Notification failed after {attempt} attempts with status {status}. Response: {text}"
                    logger.error(err)
                    return {"success": False, "status_code": status, "response": text, "error": err}

            # For client errors (4xx other than 429), do not retry
            err = f"Notification request failed with status {status}. Response: {text}"
            logger.error(err)
            return {"success": False, "status_code": status, "response": text, "error": err}

        except httpx.RequestError as exc:
            # Network-related errors are retriable
            if attempt <= retries:
                wait = backoff_factor * (2 ** (attempt - 1))
                logger.warning(f"Request error sending notification: {exc}. Retrying in {wait}s...")
                await asyncio.sleep(wait)
                continue
            else:
                err = f"Request error after {attempt} attempts: {exc}"
                logger.exception(err)
                return {"success": False, "status_code": None, "response": None, "error": err}
        except Exception as exc:
            logger.exception(f"Unexpected error when posting notification: {exc}")
            return {"success": False, "status_code": None, "response": None, "error": str(exc)}


async def send_jira_notification(
    action: str,
    issue_key: str,
    issue_url: str,
    summary: Optional[str] = None,
    description: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None,
    endpoint: Optional[str] = None,
) -> Dict[str, Any]:
    """Convenience wrapper to send a Jira-related notification payload.

    Payload includes action, issue_key, issue_url, summary, description and any extra fields.
    """
    payload = {
        "action": action,
        "issue_key": issue_key,
        "issue_url": issue_url,
        "summary": summary,
        "description": description,
    }
    if extra:
        payload["extra"] = extra

    return await post_notification(payload, endpoint=endpoint)
