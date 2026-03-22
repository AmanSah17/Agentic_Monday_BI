"""Session Management with Redis + PostgreSQL Backend"""
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
import json


class SessionManager:
    """
    Manages user sessions with:
    - Redis: Fast session state & caching
    - PostgreSQL: Persistent storage & history
    """

    def __init__(self, redis_client=None, db_connection=None):
        """
        Args:
            redis_client: Redis connection for session state
            db_connection: PostgreSQL connection for persistence
        """
        self.redis = redis_client
        self.db = db_connection
        self.session_ttl = 86400  # 24 hours

    def create_session(
        self,
        user_id: str,
        conversation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create new session"""
        session_id = str(uuid.uuid4())
        conversation_id = conversation_id or str(uuid.uuid4())

        session_data = {
            "session_id": session_id,
            "conversation_id": conversation_id,
            "user_id": user_id,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "last_activity": datetime.utcnow().isoformat() + "Z",
            "status": "active",
            "metadata": metadata or {},
            "node_traces": [],
            "messages": [],
        }

        # Store in Redis
        if self.redis:
            self.redis.setex(
                f"session:{session_id}",
                self.session_ttl,
                json.dumps(session_data),
            )

        # Store in PostgreSQL for persistence
        if self.db:
            self._persist_session(session_data)

        return session_data

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve session data"""
        # Try Redis first (cache)
        if self.redis:
            cached = self.redis.get(f"session:{session_id}")
            if cached:
                return json.loads(cached)

        # Fall back to PostgreSQL
        if self.db:
            return self._retrieve_session_from_db(session_id)

        return None

    def update_session(
        self,
        session_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update session with new data"""
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        # Update fields
        session.update(updates)
        session["last_activity"] = datetime.utcnow().isoformat() + "Z"

        # Sync to Redis
        if self.redis:
            self.redis.setex(
                f"session:{session_id}",
                self.session_ttl,
                json.dumps(session),
            )

        # Sync to PostgreSQL
        if self.db:
            self._update_session_in_db(session)

        return session

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Add message to session conversation"""
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        message = {
            "id": str(uuid.uuid4()),
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "metadata": metadata or {},
        }

        session["messages"].append(message)

        # Update session
        return self.update_session(session_id, {"messages": session["messages"]})

    def add_node_trace(
        self,
        session_id: str,
        trace: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Add node execution trace to session"""
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        if "node_traces" not in session:
            session["node_traces"] = []

        session["node_traces"].append(trace)

        return self.update_session(
            session_id, {"node_traces": session["node_traces"]}
        )

    def extend_session(self, session_id: str) -> None:
        """Extend session TTL"""
        if self.redis:
            self.redis.expire(f"session:{session_id}", self.session_ttl)

    def close_session(self, session_id: str) -> None:
        """Close and archive session"""
        session = self.get_session(session_id)
        if session:
            session["status"] = "closed"
            session["closed_at"] = datetime.utcnow().isoformat() + "Z"

            if self.db:
                self._update_session_in_db(session)

            if self.redis:
                self.redis.delete(f"session:{session_id}")

    def get_conversation_history(
        self,
        conversation_id: str,
        limit: int = 50
    ) -> list:
        """Get conversation history"""
        if not self.db:
            return []

        # Query PostgreSQL for conversation messages
        # This would depend on your actual schema
        return self._query_conversation_from_db(conversation_id, limit)

    # PostgreSQL helper methods (placeholders - implement based on your schema)
    def _persist_session(self, session_data: Dict[str, Any]) -> None:
        """Store session in PostgreSQL"""
        # TODO: Implement based on your database schema
        pass

    def _retrieve_session_from_db(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve session from PostgreSQL"""
        # TODO: Implement based on your database schema
        return None

    def _update_session_in_db(self, session_data: Dict[str, Any]) -> None:
        """Update session in PostgreSQL"""
        # TODO: Implement based on your database schema
        pass

    def _query_conversation_from_db(
        self,
        conversation_id: str,
        limit: int
    ) -> list:
        """Query conversation history from PostgreSQL"""
        # TODO: Implement based on your database schema
        return []
