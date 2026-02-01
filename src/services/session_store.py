"""In-memory session store for multi-turn conversation state"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from loguru import logger


class SessionStore:
    """
    In-memory store for session state across conversation turns.
    
    Tracks:
    - Whether session exists (first turn vs subsequent turns)
    - Similarity search results from previous turn
    - User's pending decision (create new, update existing, etc.)
    """
    
    _instance: Optional["SessionStore"] = None
    
    def __new__(cls) -> "SessionStore":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._sessions: Dict[str, Dict[str, Any]] = {}
        return cls._instance
    
    def get_or_create_session(self, session_id: str) -> Dict[str, Any]:
        """
        Get existing session or create new one.
        
        Returns:
            Session data dict with: exists, first_turn, similar_tickets, user_decision, created_at
        """
        if session_id not in self._sessions:
            self._sessions[session_id] = {
                "exists": True,
                "first_turn": True,
                "similar_tickets": [],
                "user_decision": None,  # "create_new", "update_existing", None
                "created_at": datetime.utcnow().isoformat(),
                "last_activity": datetime.utcnow().isoformat(),
            }
            logger.info(f"Created new session: {session_id}")
            return self._sessions[session_id].copy()
        
        session = self._sessions[session_id]
        session["last_activity"] = datetime.utcnow().isoformat()
        return session.copy()
    
    def session_exists(self, session_id: str) -> bool:
        """Check if session was created in a previous request."""
        return session_id in self._sessions
    
    def is_first_turn(self, session_id: str) -> bool:
        """Check if this is the first request in the session."""
        if session_id not in self._sessions:
            return True
        return self._sessions[session_id].get("first_turn", True)
    
    def mark_turn_complete(self, session_id: str):
        """Mark that first turn is done (after similarity/search)."""
        if session_id in self._sessions:
            self._sessions[session_id]["first_turn"] = False
            self._sessions[session_id]["last_activity"] = datetime.utcnow().isoformat()
    
    def store_similarity_results(
        self, session_id: str, similar_tickets: List[Dict[str, Any]]
    ):
        """Store similarity search results for the session."""
        if session_id in self._sessions:
            self._sessions[session_id]["similar_tickets"] = similar_tickets
            self._sessions[session_id]["last_activity"] = datetime.utcnow().isoformat()
    
    def get_similar_tickets(self, session_id: str) -> List[Dict[str, Any]]:
        """Get stored similarity results from previous turn."""
        if session_id not in self._sessions:
            return []
        return self._sessions[session_id].get("similar_tickets", [])
    
    def set_user_decision(self, session_id: str, decision: str):
        """Set user's decision: create_new, update_existing, etc."""
        if session_id in self._sessions:
            self._sessions[session_id]["user_decision"] = decision
            self._sessions[session_id]["last_activity"] = datetime.utcnow().isoformat()
    
    def get_user_decision(self, session_id: str) -> Optional[str]:
        """Get user's decision from context (inferred from current query)."""
        if session_id not in self._sessions:
            return None
        return self._sessions[session_id].get("user_decision")
    
    def clear_session(self, session_id: str):
        """Clear session data (e.g., after ticket created)."""
        if session_id in self._sessions:
            del self._sessions[session_id]
            logger.info(f"Cleared session: {session_id}")


# Global singleton
session_store = SessionStore()
