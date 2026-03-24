from __future__ import annotations

import json
import os
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, List, Dict, Optional

import redis
from founder_bi_agent.backend.core.config import AgentSettings
from founder_bi_agent.backend.db.postgres_db import PostgresManager

logger = logging.getLogger(__name__)

@dataclass
class HistoryStoreStatus:
    backend: str
    redis_available: bool
    ttl_seconds: int
    max_turns: int

class ConversationHistoryStore:
    """
    Hybrid History Store:
    - Redis: Fast caching for active sessions (TTL enabled)
    - PostgreSQL: Persistent long-term storage
    """

    def __init__(self, settings: AgentSettings) -> None:
        self.settings = settings
        self.ttl_seconds = int(os.getenv("SESSION_TTL_SECONDS", "86400"))
        self.max_turns = int(os.getenv("SESSION_MAX_TURNS", "30"))
        
        # Initialize PostgreSQL
        self.pg = PostgresManager(settings)
        
        # Initialize Redis with a quick socket check
        import socket
        try:
            # Quick check if port is open
            with socket.create_connection((settings.redis_host, settings.redis_port), timeout=1.0):
                pass
            
            self.redis = redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                decode_responses=True,
                socket_timeout=2,
                socket_connect_timeout=2
            )
            self.redis.ping()
            self.redis_available = True
            logger.info("Redis connected for history caching.")
        except Exception as e:
            logger.warning(f"Redis not available: {e}. Falling back to PG only.")
            self.redis_available = False

    def status(self) -> HistoryStoreStatus:
        return HistoryStoreStatus(
            backend="postgresql",
            redis_available=self.redis_available,
            ttl_seconds=self.ttl_seconds,
            max_turns=self.max_turns,
        )

    def get_history(self, session_id: str, user_id: Optional[int] = None) -> list[dict[str, str]]:
        """Retrieve history from Redis (cache) or PostgreSQL (fallback)"""
        # 1. Try Redis
        cache_key = f"hist:{session_id}"
        if user_id:
            cache_key = f"hist:{user_id}:{session_id}"
            
        if self.redis_available:
            cached = self.redis.get(cache_key)
            if cached:
                return json.loads(cached)

        # 2. Fallback to PostgreSQL
        conn = self.pg.get_connection()
        try:
            with conn.cursor() as cur:
                query = "SELECT role, content FROM conversation_history WHERE session_id = %s"
                params = [session_id]
                
                if user_id:
                    query += " AND user_id = %s"
                    params.append(user_id)
                
                query += " ORDER BY timestamp ASC"
                
                cur.execute(query, tuple(params))
                rows = cur.fetchall()
                turns = [{"role": r[0], "content": r[1]} for r in rows]
                turns = turns[-self.max_turns:] if self.max_turns > 0 else turns
                
                # Update Redis cache if available
                if self.redis_available:
                    self.redis.setex(cache_key, self.ttl_seconds, json.dumps(turns))
                
                return turns
        except Exception as e:
            logger.error(f"Failed to fetch PG history: {e}")
            return []
        finally:
            self.pg.release_connection(conn)

    def append_turns(self, session_id: str, turns: list[dict[str, str]], user_id: Optional[int] = None) -> list[dict[str, str]]:
        sanitized = self._sanitize_turns(turns)
        if not sanitized:
            return self.get_history(session_id, user_id)

        # 1. Persist to PostgreSQL
        conn = self.pg.get_connection()
        try:
            with conn.cursor() as cur:
                for turn in sanitized:
                    cur.execute(
                        """
                        INSERT INTO conversation_history (session_id, user_id, role, content)
                        VALUES (%s, %s, %s, %s)
                        """,
                        (session_id, user_id, turn["role"], turn["content"])
                    )
                conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to append PG turns: {e}")
        finally:
            self.pg.release_connection(conn)
        
        # 2. Invalidate Redis cache
        if self.redis_available:
            cache_key = f"hist:{session_id}"
            if user_id:
                cache_key = f"hist:{user_id}:{session_id}"
            self.redis.delete(cache_key)
            
        return self.get_history(session_id, user_id)

    def log_error(self, session_id: str, error_type: str, error_message: str, stack_trace: str = "", user_id: Optional[int] = None) -> None:
        conn = self.pg.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO error_logs (session_id, user_id, error_type, error_message, stack_trace)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (session_id, user_id, str(error_type), str(error_message), str(stack_trace))
                )
                conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to log PG error: {e}")
        finally:
            self.pg.release_connection(conn)

    @staticmethod
    def _sanitize_turns(turns: list[dict[str, Any]]) -> list[dict[str, str]]:
        out: list[dict[str, str]] = []
        for turn in turns:
            role = str(turn.get("role", "")).strip().lower()
            content = str(turn.get("content", "")).strip()
            if role not in {"user", "assistant", "model"}:
                continue
            if not content:
                continue
            normalized_role = "assistant" if role == "model" else role
            out.append({"role": normalized_role, "content": content})
        return out
